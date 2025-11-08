import json
import time
from glob import glob
from gzip import open as gzip_open
from itertools import chain
from json import dump, dumps, load, loads
from os import environ
from pathlib import Path
from pandas import read_xml
from statistics import mean, median
from typing import Collection, Iterator
import gzip

from chatnoir_api.model import Index
from chatnoir_api import cache_contents
from ir_datasets import load as irds_load
from pandas import DataFrame, read_csv
from pyterrier import BatchRetrieve, IndexFactory, IterDictIndexer, Transformer
from pyterrier.apply import generic
from pyterrier.io import read_results, read_topics, write_results
from chatnoir_pyterrier import ChatNoirRetrieve, Feature
from tira.rest_api_client import Client
from tqdm import tqdm
from trectools import TrecPoolMaker, TrecRun, TrecQrel


def _fetch_passage_ids(doc_id: str) -> list[str]:
    from elasticsearch_dsl import Search, connections
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
    try:
        from pyterrier_dr import Ance, TctColBert
        from pyterrier_t5 import MonoT5ReRanker
    except:
        pass
    yield "mono-t5", lambda: MonoT5ReRanker(verbose=True)
    yield "colbert", lambda: TctColBert(verbose=True)
    yield "ance", lambda: Ance(verbose=True)


def get_judgment_pool(
    pooling_path: Path,
    pooling_depth,
):
    output_path = pooling_path / "judgment-pool.json"
    if not output_path.exists():
        config_data = json.load(open(pooling_path / "config.json"))
        
        if config_data["topics"].endswith(".xml"):
            relevant_documents_per_topic = read_topics(
                filename=pooling_path / config_data["topics"],
                format="trecxml",
                tags=["relevant_docnos"],
                tokenise=False,
            )
        else:
            relevant_documents_per_topic = read_csv(pooling_path/"manual.csv")
        runs = []
        for run in glob(str(pooling_path) +"/" + config_data["runs"]):
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
            pool[str(t.qid)].add(str(t.doc_id))

        with output_path.open("wb") as file:
            file.write(dumps({k: list(v) for k, v in pool.items()}).encode("UTF-8"))

    with output_path.open("rb") as file:
        ret = load(file)
    pool_sizes = []
    for k in ret:
        pool_sizes += [len(ret[k])]
    print(
        "Pool sizes", mean(pool_sizes), "(Mean)", ";", median(pool_sizes), "(Median)."
    )
    return ret


def chatnoir_retrieve(field, topics_path, run_dir, index, model, depth):
    target_file = run_dir / f"run-chatnoir-{field}-{model}-{depth}.gz"

    if target_file.exists():
        return

    topics = load_topics(topics_path=topics_path, tag=field, tokenise=False)
    chatnoir = ChatNoirRetrieve(index=index, search_method=model, features=[], verbose=True, num_results=depth, page_size=depth)
    run = chatnoir(topics)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_results(run, target_file)
    

def get_documents(pooling_path: Path):
    config_data = json.load(open(pooling_path / "config.json"))
    run_path = pooling_path / config_data["runs"]
    documents_path = pooling_path / "documents.jsonl.gz"
    
    def docs_failsave():
        ret =  []
        try:
        
            with gzip_open(documents_path, "rt") as file:
                for line in file:
                    try:
                        ret.expand(loads(line))
                    except: pass
        except:
            pass

        return ret

    covered_docs = set([str(i["doc_id"]) for doc in docs_failsave()])

    all_docs = set()
    for file_name in glob(f"{run_path}/*.gz"):
        run = TrecRun(file_name).run_data
        for doc in run["docid"].unique():
            if doc not in covered_docs:
                all_docs.add(doc)
    print("docs size", len(all_docs))
    if len(all_docs) > 0:
        with gzip_open(documents_path, "at") as file:
            for doc in tqdm(all_docs, "Load Docs"):
                contents = cache_contents(doc, index=config_data["chatnoir-index"])
                contents = json.loads(contents)
                orig = contents["original_document"]
                file.write(dumps({"docno": contents["docno"], "text": contents["text"], "title": orig["title"], "url": orig["url"]}) + "\n")
                file.flush()

    return docs_failsave()




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
    path: Path,
    pooling_depth: int,
):
    config_data = json.load(open(path / "config.json"))
    topics_path = path / config_data["topics"]
    run_path = path / config_data["runs"]

    get_documents(path)
    raise ValueError("fooo")
    chatnoir_retrieve("title", topics_path, run_path, config_data["chatnoir-index"], "bm25", 1000)
    chatnoir_retrieve("description", topics_path, run_path, config_data["chatnoir-index"], "bm25", 1000)
    chatnoir_retrieve("title", topics_path, run_path, config_data["chatnoir-index"], "default", 25)
    chatnoir_retrieve("description", topics_path, run_path, config_data["chatnoir-index"], "default", 25)

    raise ValueError("sa")
    judgment_pool = get_judgment_pool(
        pooling_path=path,
        pooling_depth=pooling_depth
    )

    doccano_judgment_pool_path = path / "doccano-judgment-pool.jsonl"
    if doccano_judgment_pool_path.exists():
        print(f'Exists "{doccano_judgment_pool_path}". I do not override')
        return

    if str(topics_path).endswith(".xml"):
        topic_to_title = load_topics_dict(
            topics_path=topics_path,
            tag="title",
            tokenise=False,
        )
        topic_to_group = load_topics_dict(
            topics_path=topics_path,
            tag="group",
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
    else:
        topic_to_title = {}
        topic_to_description = {}
        topic_to_narrative = {}
        print(topics_path)
        for _, i in read_csv(topics_path).iterrows():
            print(i)
            raise ValueError(i["qid"], i["query"])
            qid = str(i["qid"])
            topic_to_title[qid] = i["query"]
            topic_to_description[qid] = i["description"]
            topic_to_narrative[qid] = i["narrative"]

    with doccano_judgment_pool_path.open("wt") as file:
        if 'irds-id' in config_data:
            docs_store = irds_load(config_data["irds-id"]).docs_store()
        else:
            docs_store = {}
            with gzip.open(path / "corpus.jsonl.gz", "rt") as f:
                for l in f:
                    l = json.loads(l)
                    docs_store[l["doc_id"]] = l

        with open(path / "topic-mapping.jsonl", "r") as f:
            doc_count = 0
            no_main_content = 0
            skipped_long = 0
            for i in f:
                i = json.loads(i)
                group = i["account"]
                for topic in i["topics"]:
                    for document in judgment_pool[topic]:
                        if document not in docs_store:
                            print(f"Skip document with id {document}")
                            continue
                        from bs4 import BeautifulSoup
                        main_content = BeautifulSoup(docs_store.get(document)["main_content"], features="html.parser").get_text()
                        if len(main_content) < 10:
                            main_content = "No Main Content"
                            no_main_content += 1
                        if len(main_content) > 7*1000:
                            main_content = main_content[:7*1000]
                            skipped_long += 1
                        doc_count += 1
                        file.write(
                            dumps(
                                {
                                    "group": group,
                                     "query_id": topic,
                                     "query": topic_to_title[topic],
                                     "description": topic_to_description[topic],
                                     "narrative": topic_to_narrative[topic],
                                     "doc_id": document,
                                     "url": docs_store.get(document)["url"],
                                     "title": docs_store.get(document)["title"],
                                     "text": main_content,
                        }
                    )
                    + "\n"
                )
            print(f"Docs to judge {doc_count}. No main content {no_main_content}. Truncated: {skipped_long}")


def read_tira_invites(invite_path: Path):
    if not invite_path.exists():
        with open(invite_path, "w") as f:
            f.write("{}")

    with open(invite_path, "r") as f:
        return json.load(f)

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
    meta_data = json.load(open(pooling_path / 'metadata.json'))
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
            f.write(json.dumps({"docno": doc, "text": doc_text}) + '\n')
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
        time.sleep(1)
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
        time.sleep(1)
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
        time.sleep(8)

    print(
        group_name
        + ": "
        + json.dumps(all_invites[group_name]["context"]["created_group"])
    )
