#from chatnoir_api.cache import term_vectors
import pyterrier as pt
import os
import json
from tqdm import tqdm
import ir_datasets
import gzip
from glob import glob
from trectools import TrecRun, TrecPoolMaker
from statistics import mean, median

if not pt.started():
    pt.init()

def passage_ids(doc_id):
    from elasticsearch_dsl import connections, Search
    try:
        connections.get_connection()
    except:
        connections.configure(default={'hosts': ['https://elasticsearch.srv.webis.de:9200'], 'retry_on_timeout': True, 'http_auth': (os.environ['ES_USER'], os.environ['ES_PASSWORD']), 'timeout': 30})
    
    ret = set()
    results = Search().index('chatnoir_meta_complete_msmarco_document_v2.1_segmented').query("prefix", warc_trec_id=doc_id + '#')
    for i in results:
        ret.add(i.warc_trec_id)
    
    return sorted(list(ret))

def all_re_rankers():
    try:
        from pyterrier_t5 import MonoT5ReRanker
        import pyterrier_dr
    except: pass

    return [
        ('mono-t5', lambda: MonoT5ReRanker()),
        ('colbert', lambda: pyterrier_dr.TctColBert(verbose=True)),
        ('ance', lambda: pyterrier_dr.Ance(verbose=True))
    ]

def get_judgment_pool(directory, pooling_depth, all_docs):
    output_file = f'{directory}/judgment-pool.json'
    if not os.path.exists(output_file):
        relevant_documents_per_topic = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=['relevant_docnos'], tokenise=False)
        runs = []
        for run in glob(f'{directory}/pyterrier-*-run.gz') + glob(f'{directory}/neural-*-run.gz'):
            runs += [TrecRun(run)]

        pool = TrecPoolMaker().make_pool(runs, strategy="topX", topX=pooling_depth).pool
        pool_sizes = []
        for k in pool:
            pool_sizes += [len(pool[k])]

        print('Pool sizes', mean(pool_sizes), '(Mean)', ';', median(pool_sizes), '(Median).') 

        for _, t in tqdm(list(relevant_documents_per_topic.iterrows()), 'Expansion Docs'):
            docs_for_query = set()
            relevant_docnos = set([i.strip() for i in t['query'].split(',')])
            relevant_docnos = sorted([i for i in relevant_docnos if len(i) > 3])

            for relevant_doc in relevant_docnos:
                found = False
                for doc in all_docs:
                    if doc.startswith(relevant_doc + '#'):
                        docs_for_query.add(doc)
                        found = True
                if not found:
                    for doc in passage_ids(relevant_doc):
                        docs_for_query.add(doc)
            for doc in docs_for_query:
                pool[t.qid].add(doc)

            if len(docs_for_query) == 0 and len(relevant_docnos) != 0:
                print('Missing relevant docs for topic', relevant_docnos)

        json.dump({k: list(v) for k,v in pool.items()}, open(output_file, 'w'))

    ret = json.load(open(output_file, 'r'))
    pool_sizes = []
    for k in ret:
        pool_sizes += [len(ret[k])]
    print('Pool sizes', mean(pool_sizes), '(Mean)', ';', median(pool_sizes), '(Median).')
    return ret


def get_documents(directory):
    if not os.path.exists(f'{directory}/documents.jsonl.gz'):
        docs_store = ir_datasets.load('msmarco-segment-v2.1').docs_store()
        with gzip.open(f'{directory}/documents.jsonl.gz', 'wt') as f:
            for doc in tqdm(all_docs, 'Load Docs'):
                doc = docs_store.get(doc)
                f.write(json.dumps({'docno': doc.doc_id, 'text': doc.default_text()}) + '\n')
                f.flush()

    ret = []

    with gzip.open(f'{directory}/documents.jsonl.gz', 'rt') as f:
        for l in f:
            ret += [json.loads(l)]
    return ret

def get_index(directory):
    if not os.path.exists(f'{directory}/pyterrier-index'):
        documents = get_documents(directory)

        indexer = pt.IterDictIndexer(os.path.abspath(f'{directory}/pyterrier-index'), meta={'docno': 100, 'text': 20480})
        index_ref = indexer.index(tqdm(documents, 'Index'))

    return pt.IndexFactory.of(os.path.abspath(f'{directory}/pyterrier-index'))

def load_topics(directory, tag, tokenise, as_dataframe):
    ret = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=[tag], tokenise=tokenise)
    
    if as_dataframe:
        return ret
    else:
        return {i['qid']: i['query'] for _, i in ret.iterrows()}
        

def main(directory, retrieval_index, feedback_index, corpus_offset, pooling_depth):
    for query_type in ['title', 'description']:
        topics = load_topics(directory, query_type, tokenise=False, as_dataframe=True)

        for retrieval_model in ['default', 'bm25']:
            output_file = f'{directory}/corpus-chatnoir-{retrieval_model}-on-{query_type}-run.gz'
            if os.path.exists(output_file):
                continue
            from chatnoir_pyterrier import ChatNoirRetrieve
            chatnoir = ChatNoirRetrieve(index=retrieval_index, retrieval_system=retrieval_model, num_results=1500, verbose=True)
            results = chatnoir(topics)
            pt.io.write_results(results, output_file)

    if not os.path.exists(f'{directory}/reformulated-feedback-documents.jsonl'):
        with open(f'{directory}/reformulated-feedback-documents.jsonl', 'w') as f:
            json.dump({}, f)

#    for _, t in tqdm(list(relevant_documents_per_topic.iterrows()), 'Expansion Docs'):
#        relevant_docnos = t['query'].split(',')
#        for relevant_doc in relevant_docnos:
#            reformulated_documents = json.load(open(f'{directory}/reformulated-feedback-documents.jsonl', 'r'))
#            if relevant_doc in reformulated_documents:
#                continue
#
#            relevant_doc = relevant_doc.strip()
#            if len(relevant_doc) < 3:
#                continue
#            tf = term_vectors(trec_id=relevant_doc, index=feedback_index)

    all_docs = set()
    for query_type in ['title', 'description']:
        for retrieval_model in ['default', 'bm25']:
            output_file = f'{directory}/corpus-chatnoir-{retrieval_model}-on-{query_type}-run.gz'
            results = pt.io.read_results(output_file)
            results = results[results['rank'] <= corpus_offset]
            for doc in results['docno']:
                all_docs.add(doc)
    print('Corpus-size', len(all_docs))

    for retrieval_model in ['BM25', 'PL2', 'DirichletLM', 'TF_IDF', 'Hiemstra_LM']:
        output_file = f'{directory}/pyterrier-{retrieval_model}-run.gz'
        if os.path.exists(output_file):
            continue
        index = get_index(directory)
        retriever = pt.BatchRetrieve(index, wmodel=retrieval_model)
        topics = load_topics(directory, 'title', tokenise=True, as_dataframe=True)
        results = retriever(topics)
        pt.io.write_results(results, output_file)

    for retrieval_model, reranker in tqdm(all_re_rankers(), 'Re-Rankers'):
        for query_type in ['title', 'description']:
            output_file = f'{directory}/neural-{retrieval_model}-on{query_type}-run.gz'
            if os.path.exists(output_file):
                continue

            documents = {i['docno']: i['text'] for i in get_documents(directory)}

            def add_text(df):
                df['text'] = df['docno'].apply(lambda i: documents[i])
                return df

            topics = load_topics(directory, query_type, tokenise=False, as_dataframe=True)
            first_stage = pt.io.read_results(f'{directory}/pyterrier-BM25-run.gz')
            first_stage = pt.transformer.get_transformer(first_stage)
            first_stage = first_stage >> pt.apply.generic(add_text) >> reranker()

            results = first_stage(topics)
            pt.io.write_results(results, output_file)

    judgment_pool = get_judgment_pool(directory, pooling_depth, all_docs)

    topic_to_title = load_topics(directory, 'title', tokenise=False, as_dataframe=False)
    topic_to_description = load_topics(directory, 'description', tokenise=False, as_dataframe=False)
    topic_to_narrative = load_topics(directory, 'narrative', tokenise=False, as_dataframe=False)

    with open(f'{directory}/doccano-judgment-pool.jsonl', 'w') as f:
        docs_store = ir_datasets.load('msmarco-segment-v2.1').docs_store()

        for topic in tqdm(judgment_pool, 'Doccano Pool'):
            for document in judgment_pool[topic]:
                f.write(json.dumps({
                    "group": f'ir-wise-24-{topic}',
                    "query_id": topic,
                    "query": topic_to_title[topic],
                    "description": topic_to_description[topic],
                    "narrative": topic_to_narrative[topic],
                    "doc_id": document,
                    "text": docs_store.get(document).default_text(),
                }) + '\n')

