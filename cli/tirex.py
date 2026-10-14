from dataclasses import dataclass
from functools import reduce
from gzip import open as gzip_open
from json import  dumps, load, loads
from pathlib import Path
from time import sleep
from typing import Any

from chatnoir_api import cache_contents, Index
from chatnoir_pyterrier import ChatNoirRetrieve, Feature
from ir_datasets import load as irds_load
from pandas import DataFrame, read_csv, read_xml, concat
from pyterrier import IndexFactory, IterDictIndexer, Indexer, Transformer
from pyterrier.io import read_topics
from pyterrier.terrier import Retriever
from pyterrier.terrier.rewrite import tokenise
from pyterrier_caching import RetrieverCache
from tira.rest_api_client import Client
from tqdm import tqdm
from trectools import TrecPoolMaker, TrecRun, TrecQrel


@dataclass(frozen=True)
class ChatNoirContents(Transformer):
    """PyTerrier transformer to get document contents from ChatNoir cache based on the document ID."""

    index: Index

    def transform(self, inp: DataFrame) -> DataFrame:
        docs = []
        for _, row in tqdm(
            inp.iterrows(), 
            total=len(inp), 
            desc="Get contents",
        ):
            docno = row["docno"]
            contents = cache_contents(docno, index=self.index)
            contents = loads(contents)
            docs.append(
                {
                    **row.to_dict(),
                    "text": contents["text"],
                    "title": contents["original_document"]["title"],
                    "url": contents["original_document"]["url"],
                }
            )
        return DataFrame(docs)


def pool_documents(
    topics_path: Path,
    pooling_path: Path,
    chatnoir_index: Index,
    pooling_depth: int,
    cache_path: Path,
    chatnoir_default_depth: int = 10,
    chatnoir_bm25_depth: int = 1000,
) -> None:
    # Use both title and description topics for retrieval (and ensure unique qids).
    topics = concat([
        read_topics(
            filename=str(topics_path),
            format="trecxml",
            tags=["title"],
            tokenise=False,
        ).assign(
            qid=lambda df: df["qid"] + "_title"
        ),
        read_topics(
            filename=str(topics_path),
            format="trecxml",
            tags=["description"],
            tokenise=False,
        ).assign(
            qid=lambda df: df["qid"] + "_description"
        ),
    ])
    topics = topics.head(5)  # TODO remove

    # Step 1: Retrieve candidate documents from ChatNoir using different retrieval methods (ChatNoir default BM25F and plain BM25) and topics (title and description).
    candidate_retreivers = [
        RetrieverCache(
            cache_path / f"chatnoir-default-top-{chatnoir_default_depth}",
            ChatNoirRetrieve(
                index=chatnoir_index, 
                search_method="default",
                verbose=True,
                num_results=chatnoir_default_depth,
                features=Feature.NONE
            ),
            on="qid",
            # verbose=True,
        ),
        RetrieverCache(
            cache_path / f"chatnoir-bm25-top-{chatnoir_bm25_depth}",
            ChatNoirRetrieve(
                index=chatnoir_index, 
                search_method="bm25",
                verbose=True,
                num_results=chatnoir_bm25_depth,
                features=Feature.NONE
            ),
            on="qid",
            # verbose=True,
        ),
    ]
    # Compute the set union of retrieved documents.
    candidate_retriever: Transformer = reduce(
        lambda a, b: a | b,
        candidate_retreivers,
    )
    # Retrieve candidate documents and get unique document IDs.
    candidate_document_ids = candidate_retriever.transform(topics)[["docno"]].drop_duplicates()
    print(f"Retreived {len(candidate_document_ids)} candidate documents (IDs).")

    # Step 2: Fetch document contents from ChatNoir for the candidate document IDs.
    chatnoir_contents = RetrieverCache(
        cache_path / "chatnoir-contents",
        ChatNoirContents(index=chatnoir_index),
        on="docno",
        verbose=True,
    )
    candidate_documents = chatnoir_contents.transform(candidate_document_ids)
    print(f"Fetched contents of {len(candidate_documents)} candidate documents.")

    # Step 3: Index the candidate documents using PyTerrier for further processing.
    index_path = cache_path / "index"
    index_path = index_path.resolve()
    index_ref: Any
    if not index_path.exists() or not any(index_path.iterdir()):
        indexer: Indexer = IterDictIndexer(
            str(index_path),
            meta={
                "docno": 100,
                "text": 20480,
            },
        )
        index_ref = indexer.index(row for _, row in candidate_documents.iterrows())  # type: ignore
    else:
        index_ref = IndexFactory.of(str(index_path))  # type: ignore
    print(f"Indexed candidate documents at {index_path}.")

    # Step 4: Retrieve documents from the indexed candidate documents using various retrieval models and topics (title and description).
    retrievers = [
        tokenise() >> RetrieverCache(
            cache_path / f"pyterrier-{model}-top-1000",
            Retriever(index_ref, wmodel=model, num_results=1000, verbose=True),
            on="qid",
            # verbose=True,
        )
        for model in ["BM25", "PL2", "TF_IDF", "DirichletLM", "Hiemstra_LM", "DFRee", "Dl", "DLH", "DPH", "Tf", "LGD"]
    ] + candidate_retreivers
    # Cut off retrievers at pooling depth.
    retrievers = [retriever % pooling_depth for retriever in retrievers]
    # Compute the set union of retrieved documents.
    retriever: Transformer = reduce(
        lambda a, b: a | b,
        retrievers,
    )
    # Retrieve candidate documents and get unique document IDs.
    document_ids = retriever.transform(topics)[["qid", "docno"]].drop_duplicates()
    print(f"Retreived {len(document_ids)} documents (IDs).")

    # Step 5: Add manually specified relevant documents to the final document IDs.
    manual_relevant_document_ids = (
        read_xml(topics_path)
        .rename(columns={"number": "qid", "relevant_docnos": "docno"})[["qid", "docno"]]
        .assign(docno=lambda df: df["docno"].str.split(","))
        .explode("docno")
        .drop_duplicates()
        .dropna())
    print(f"Adding {len(manual_relevant_document_ids)} manually specified relevant documents.")
    print(manual_relevant_document_ids)

    document_ids = concat([document_ids, manual_relevant_document_ids]).drop_duplicates()
    print(f"Got {len(document_ids)} final documents (IDs).")

    # Step 6: Fetch document contents from ChatNoir for the final document IDs.
    documents = chatnoir_contents.transform(document_ids)
    print(f"Fetched contents of {len(documents)} documents.")
    print(documents.columns)

    # Step 7: Add topic metadata (title, description, narrative).
    topics_metadata = (
        read_xml(topics_path)
        .rename(columns={"number": "qid", "title": "query"})[["qid", "query", "description", "narrative"]])
    print(topics_metadata)
    documents = documents.merge(
        topics_metadata,
        how="left",
        on="qid",
    )

    # Step 8: Filter documents without text or with long text.
    filter_no_text = documents["text"].isna()
    documents = documents[~filter_no_text]
    print(f"Filtered out {filter_no_text.sum()} documents without text ({len(documents)} documents remaining).")
    filter_too_short = documents["text"].str.len() < 10
    documents = documents[~filter_too_short]
    print(f"Filtered out {filter_too_short.sum()} documents with text shorter than 10 characters ({len(documents)} documents remaining).")
    filter_too_long = documents["text"].str.len() > 7000
    documents = documents[~filter_too_long]
    print(f"Filtered out {filter_too_long.sum()} documents with text longer than 7000 characters ({len(documents)} documents remaining).")

    # Step 9: Save the judgment pool.
    documents.to_json(pooling_path, orient="records", lines=True)


def read_tira_invites(invite_path: Path):
    if not invite_path.exists():
        with open(invite_path, "w") as f:
            f.write("{}")

    with open(invite_path, "r") as f:
        return load(f)

def to_xml_query(query):
    appendix = ""
    try:
        appendix = f"""  <description>{query.description}</description>
  <narrative>{query.narrative}</narrative>
"""
    except:
        pass

    return f""" <topic number="{query.query_id}">
  <query>
   {query.default_text()}
  </query>
  <original_query>
   <query_id>
     {query.query_id}
   </query_id>{appendix}
   <text>
     {query.default_text()}
   </text>
  </original_query>
 </topic>
"""

def to_jsonl_query(query):
    ret = {"qid": query.query_id, "query": query.default_text()}
    ret["original_query"] = ret.copy()
    return json.dumps(ret)

def subsample_corpus(qrels_path: Path, pooling_path: Path, pooling_depth: int):
    inputs_dir = pooling_path / 'subsampled-dataset' / 'inputs'
    truths_dir = pooling_path / 'subsampled-dataset' / 'truths'
    if (inputs_dir / 'documents.jsonl.gz').exists():
        return
    meta_data = load(open(pooling_path / 'metadata.json'))
    dataset = irds_load(meta_data['ir_datasets_id'])
    docs_store = dataset.docs_store()
    queries_dict = {}
    
    if dataset.has_queries():
        for i in dataset.queries_iter():
            assert i.query_id not in queries_dict
            queries_dict[i.query_id] = i
    else:
        queries_df = read_xml(qrels_path.parent / 'topics.xml', dtype=str).rename(columns={"number": "query_id"})
        for _, i in queries_df.iterrows():
            i = i.to_dict()
            class TmpQuery():
                def __init__(self, i):
                    self.title = i["title"]
                    self.query_id = i["query_id"]
                    self.narrative = i["narrative"]
                    self.description = i["description"]

                def default_text(self):
                    return self.title

            i = TmpQuery(i)
            queries_dict[i.query_id] = i

    qrels = TrecQrel(qrels_path)
    query_ids = set([i for i in qrels.qrels_data['query'].unique()])
    qrels_run = TrecRun()
    qrels_run.run_data = qrels.qrels_data.copy()
    del qrels_run.run_data['rel']
    qrels_run.run_data["rank"] = 1
    qrels_run.run_data["rank"] = qrels_run.run_data.groupby("query")["rank"].cumsum()
    qrels_run.run_data["score"] = 1000 - qrels_run.run_data["rank"]

    runs = []
    for run in tqdm(pooling_path.glob("*-run.gz")):
        runs += [TrecRun(run)]

    runs += [qrels_run]
    pool = TrecPoolMaker().make_pool(runs, strategy='topX', topX=pooling_depth).pool
    all_docs = set()

    queries_jsonl_format = []
    queries_xml_format = []
    for q in pool.keys():
        if str(q) not in query_ids:
            continue

        queries_jsonl_format += [to_jsonl_query(queries_dict[q])]
        queries_xml_format += [to_xml_query(queries_dict[q])]

        for doc in pool[q]:
            all_docs.add(doc)

    inputs_dir.mkdir(exist_ok=True, parents=True)
    truths_dir.mkdir(exist_ok=True, parents=True)
    for json_file in [inputs_dir / 'queries.jsonl', truths_dir / 'queries.jsonl' ]:
        with open(json_file, 'w') as f:
            f.write('\n'.join(queries_jsonl_format))

    for xml_file in [inputs_dir / 'queries.xml', truths_dir / 'queries.xml' ]:
        with open(xml_file, 'w') as f:
            f.write('<topics>\n' + ''.join(queries_xml_format) + '\n</topics>')

    print('Docs:' + str(len(all_docs)))
    with gzip_open(inputs_dir / 'documents.jsonl.gz', 'wt') as f:
        for doc in tqdm(all_docs):
            try:
                doc_text = docs_store.get(doc).default_text()
            except:
                print('skip due to error')
                continue
            f.write(dumps({"docno": doc, "text": doc_text}) + '\n')
            f.flush()


def create_group(
    invite_path: Path,
    tira_task_id: str,
    group_name: str,
    affiliation: str,
    country: str,
):
    all_invites = read_tira_invites(invite_path)
    tira = Client()
    if group_name not in all_invites:
        metadata_for_task = tira.metadata_for_task(tira_task_id)
        sleep(1)
        metadata_for_task = metadata_for_task["context"]["task"]
        allowed_teams = [
            i.strip() for i in metadata_for_task["allowed_task_teams"].split("\n")
        ] + [group_name]
        task_modification = {
            "featured": True,
            "require_registration": True,
            "require_groups": True,
            "restrict_groups": True,
            "task_teams": "\n".join(allowed_teams),
        }
        tira.modify_task(tira_task_id, task_modification)
        sleep(1)
        invite = tira.register_group(
            group_name,
            tira_task_id,
            name="no-name",
            email="no-mail",
            affiliation=affiliation,
            country=country,
        )
        all_invites[group_name] = invite

        with open(invite_path, "w") as f:
            f.write(json.dumps(all_invites))
        all_invites = read_tira_invites(invite_path)
        sleep(8)

    print(
        group_name
        + ": "
        + dumps(all_invites[group_name]["context"]["created_group"])
    )
