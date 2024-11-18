from gzip import open as gzip_open
from itertools import chain
from json import dump, load, dumps, loads
from os import environ
from pathlib import Path
from statistics import mean, median
from typing import Collection, Iterator

from chatnoir_api.model import Index
from ir_datasets import load as irds_load
from pandas import DataFrame
from pyterrier import Transformer, IterDictIndexer, IndexFactory, BatchRetrieve
from pyterrier.io import read_topics, write_results, read_results
from pyterrier.apply import generic
from tqdm import tqdm
from glob import glob
from trectools import TrecRun, TrecPoolMaker


def _fetch_passage_ids(doc_id: str) -> list[str]:
    from elasticsearch_dsl import connections, Search
    from elasticsearch_dsl.query import Prefix

    try:
        connections.get_connection()
    except KeyError:
        # FIXME: The Elasticsearch connection should not be hardcoded.
        connections.configure(
            default={
                "hosts": ["https://elasticsearch.srv.webis.de:9200"],
                "retry_on_timeout": True,
                "http_auth": (environ["ES_USER"], environ["ES_PASSWORD"]),
                "timeout": 30,
            }
        )

    # FIXME: The Elasticsearch index should not be hardcoded.
    results = (
        Search()
        .index("chatnoir_meta_complete_msmarco_document_v2.1_segmented")
        .query(Prefix(warc_trec_id=f"{doc_id}#"))
    )
    ids = {result.warc_trec_id for result in results}
    return sorted(ids)


def _iter_re_rankers() -> Iterator[tuple[str, Transformer]]:
    from pyterrier_t5 import MonoT5ReRanker
    from pyterrier_dr import TctColBert, Ance

    yield "mono-t5", lambda: MonoT5ReRanker(verbose=True)
    yield "colbert", lambda: TctColBert(verbose=True)
    yield "ance", lambda: Ance(verbose=True)


def get_judgment_pool(
    pooling_path: Path,
    topics_path: Path,
    pooling_depth,
    all_doc_ids: set[str],
):
    output_path = pooling_path / "judgment-pool.json"
    if not output_path.exists():
        relevant_documents_per_topic = read_topics(
            filename=str(topics_path),
            format="trecxml",
            tags=["relevant_docnos"],
            tokenise=False,
        )
        runs = []
        for run in chain(
            pooling_path.glob("pyterrier-*-run.gz"),
            pooling_path.glob("neural-*-run.gz"),
        ):
            runs += [TrecRun(run)]

        pool = TrecPoolMaker().make_pool(runs, strategy="topX", topX=pooling_depth).pool
        pool_sizes = []
        for k in pool:
            pool_sizes += [len(pool[k])]

        print(
            "Pool sizes",
            mean(pool_sizes),
            "(Mean)",
            ";",
            median(pool_sizes),
            "(Median).",
        )

        for _, t in tqdm(
            list(relevant_documents_per_topic.iterrows()), "Expansion Docs"
        ):
            doc_ids_for_query = set()
            relevant_docnos: Collection[str] = set(
                [i.strip() for i in t["query"].split(",")]
            )
            relevant_docnos = sorted([i for i in relevant_docnos if len(i) > 3])

            for relevant_doc in relevant_docnos:
                found = False
                for doc_id in all_doc_ids:
                    if doc_id.startswith(relevant_doc + "#"):
                        doc_ids_for_query.add(doc_id)
                        found = True
                if not found:
                    for doc_id in _fetch_passage_ids(relevant_doc):
                        doc_ids_for_query.add(doc_id)
            for doc_id in doc_ids_for_query:
                pool[t.qid].add(doc_id)

            if len(doc_ids_for_query) == 0 and len(relevant_docnos) != 0:
                print("Missing relevant docs for topic", relevant_docnos)

        with output_path.open("wb") as file:
            dump({k: list(v) for k, v in pool.items()}, file)

    with output_path.open("rb") as file:
        ret = load(file)
    pool_sizes = []
    for k in ret:
        pool_sizes += [len(ret[k])]
    print(
        "Pool sizes", mean(pool_sizes), "(Mean)", ";", median(pool_sizes), "(Median)."
    )
    return ret


def get_documents(pooling_path: Path):
    documents_path = pooling_path / "documents.jsonl.gz"
    if not documents_path.exists():
        docs_store = irds_load("msmarco-segment-v2.1").docs_store()
        all_docs = set()
        for file_name in glob(f'{pooling_path}/corpus-chatnoir*run.gz'):
            run = TrecRun(file_name).run_data
            for doc in run['docid']:
                all_docs.add(doc)
        print('docs size', len(all_docs))


        with gzip_open(documents_path, "wt") as file:
            for doc in tqdm(all_docs, "Load Docs"):
                doc = docs_store.get(doc)
                file.write(
                    dumps({"docno": doc.doc_id, "text": doc.default_text()}) + "\n"
                )
                file.flush()

    ret = []

    with gzip_open(documents_path, "rt") as file:
        for line in file:
            ret += [loads(line)]
    return ret


def get_index(pooling_path: Path):
    index_path = pooling_path / "pyterrier-index"
    if not index_path.exists():
        documents = get_documents(pooling_path)

        indexer = IterDictIndexer(
            str(index_path.absolute()),
            meta={"docno": 100, "text": 20480},
        )
        indexer.index(tqdm(documents, "Index"))

    return IndexFactory.of(str(index_path.absolute()))


def load_topics(
    topics_path: Path,
    tag: str,
    tokenise: bool,
) -> DataFrame:
    return read_topics(
        filename=str(topics_path),
        format="trecxml",
        tags=[tag],
        tokenise=tokenise,
    )


def load_topics_dict(
    topics_path: Path,
    tag: str,
    tokenise: bool,
):
    ret = load_topics(
        topics_path=topics_path,
        tag=tag,
        tokenise=tokenise,
    )
    return {row["qid"]: row["query"] for _, row in ret.iterrows()}


def pool_documents(
    pooling_path: Path,
    topics_path: Path,
    retrieval_index: Index,
    feedback_index: Index,
    corpus_offset: int,
    pooling_depth: int,
):
    for query_type in ("title", "description"):
        topics = load_topics(
            topics_path,
            query_type,
            tokenise=False,
        )

        for retrieval_model in ["default", "bm25"]:
            output_path = (
                pooling_path
                / f"corpus-chatnoir-{retrieval_model}-on-{query_type}-run.gz"
            )
            if output_path.exists():
                continue
            from chatnoir_pyterrier import ChatNoirRetrieve

            chatnoir = ChatNoirRetrieve(
                index=retrieval_index,
                retrieval_system=retrieval_model,
                num_results=1500,
                verbose=True,
            )
            results = chatnoir(topics)
            write_results(results, str(output_path))

    reformulated_feedback_documents_path = (
        pooling_path / "reformulated-feedback-documents.jsonl"
    )
    if not reformulated_feedback_documents_path.exists():
        with reformulated_feedback_documents_path.open("wt") as file:
            dump({}, file)

    #    for _, t in tqdm(list(relevant_documents_per_topic.iterrows()), 'Expansion Docs'):
    #        relevant_docnos = t['query'].split(',')
    #        for relevant_doc in relevant_docnos:
    #            reformulated_documents = load(open(f'{directory}/reformulated-feedback-documents.jsonl', 'r'))
    #            if relevant_doc in reformulated_documents:
    #                continue
    #
    #            relevant_doc = relevant_doc.strip()
    #            if len(relevant_doc) < 3:
    #                continue
    #            tf = term_vectors(trec_id=relevant_doc, index=feedback_index)

    all_doc_ids: set[str] = set()
    for query_type in ["title", "description"]:
        for retrieval_model in ["default", "bm25"]:
            output_path = (
                pooling_path
                / f"corpus-chatnoir-{retrieval_model}-on-{query_type}-run.gz"
            )
            results = read_results(str(output_path))
            results = results[results["rank"] <= corpus_offset]
            for doc in results["docno"]:
                all_doc_ids.add(doc)
    print("Corpus-size", len(all_doc_ids))

    for retrieval_model in ["BM25", "PL2", "DirichletLM", "TF_IDF", "Hiemstra_LM"]:
        output_path = pooling_path / f"pyterrier-{retrieval_model}-run.gz"
        if output_path.exists():
            continue
        index = get_index(pooling_path)
        retriever = BatchRetrieve(index, wmodel=retrieval_model)
        topics = load_topics(
            topics_path=topics_path,
            tag="title",
            tokenise=True,
        )
        results = retriever(topics)
        write_results(results, str(output_path))

    for retrieval_model, reranker in tqdm(
        iterable=_iter_re_rankers(),
        desc="Re-Rankers",
    ):
        for query_type in ["title", "description"]:
            output_path = (
                pooling_path / f"neural-{retrieval_model}-on{query_type}-run.gz"
            )
            if output_path.exists():
                continue

            documents = {
                i["docno"]: i["text"] for i in get_documents(pooling_path=pooling_path)
            }

            def add_text(df: DataFrame) -> DataFrame:
                df["text"] = df["docno"].apply(lambda i: documents[i])
                return df

            topics = load_topics(
                topics_path=topics_path,
                tag=query_type,
                tokenise=False,
            )
            first_stage = read_results(str(pooling_path / "pyterrier-BM25-run.gz"))
            first_stage = Transformer.from_df(first_stage)
            first_stage = first_stage >> generic(add_text)
            first_stage = first_stage >> reranker()

            results = first_stage(topics)
            write_results(results, str(output_path))

    judgment_pool = get_judgment_pool(
        pooling_path=pooling_path,
        topics_path=topics_path,
        pooling_depth=pooling_depth,
        all_doc_ids=all_doc_ids,
    )

    doccano_judgment_pool_path = pooling_path / "doccano-judgment-pool.jsonl"
    if doccano_judgment_pool_path.exists():
        print(f'Exists "{doccano_judgment_pool_path}". I do not override')
        return

    topic_to_title = load_topics_dict(
        topics_path=topics_path,
        tag="title",
        tokenise=False,
    )
    topic_to_description = load_topics_dict(
        topics_path=topics_path,
        tag="description",
        tokenise=False,
    )
    topic_to_narrative = load_topics_dict(
        topics_path=topics_path,
        tag="narrative",
        tokenise=False,
    )

    with doccano_judgment_pool_path.open("wt") as file:
        docs_store = irds_load("msmarco-segment-v2.1").docs_store()

        for topic in tqdm(judgment_pool, "Doccano Pool"):
            for document in judgment_pool[topic]:
                file.write(
                    dumps(
                        {
                            "group": f"{topic}",
                            "query_id": topic,
                            "query": topic_to_title[topic],
                            "description": topic_to_description[topic],
                            "narrative": topic_to_narrative[topic],
                            "doc_id": document,
                            "text": docs_store.get(document).default_text(),
                        }
                    )
                    + "\n"
                )
