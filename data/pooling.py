#!/usr/bin/env python3
import click
from chatnoir_pyterrier import ChatNoirRetrieve
#from chatnoir_api.cache import term_vectors
import pyterrier as pt
import os
import json
from tqdm import tqdm
import ir_datasets
import gzip

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
    from pyterrier_t5 import MonoT5ReRanker
    import pyterrier_dr
    return [
        ('mono-t5', lambda: MonoT5ReRanker()),
        ('colbert', lambda: pyterrier_dr.TctColBert(verbose=True))
        ('ance', lambda: pyterrier_dr.Ance(verbose=True))
    ]


@click.command('pooling')
@click.option('--retrieval-index', default='msmarco-passage-v2.1', help='The chatnoir index for pooling.')
@click.option('--corpus-offset', default=1500, help='The offset for the corpus.')
@click.option('--feedback-index', default='msmarco-document-v2.1', help='The chatnoir index on which feedback-documents are labeled.')
@click.argument('directory')
def main(directory, retrieval_index, feedback_index, corpus_offset):
    for query_type in ['title', 'description']:
        topics = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=[query_type], tokenise=False)

        for retrieval_model in ['default', 'bm25']:
            output_file = f'{directory}/corpus-chatnoir-{retrieval_model}-on-{query_type}-run.gz'
            if os.path.exists(output_file):
                continue
            chatnoir = ChatNoirRetrieve(index=retrieval_index, retrieval_system=retrieval_model, num_results=1500, verbose=True)
            results = chatnoir(topics)
            pt.io.write_results(results, output_file)

    relevant_documents_per_topic = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=['relevant_docnos'], tokenise=False)


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
    
    if not os.path.exists(f'{directory}/pyterrier-index'):
        if not os.path.exists(f'{directory}/documents.jsonl.gz'):
            docs_store = ir_datasets.load('msmarco-segment-v2.1').docs_store()
            with gzip.open(f'{directory}/documents.jsonl.gz', 'wt') as f:
                for doc in tqdm(all_docs, 'Load Docs'):
                    doc = docs_store.get(doc)
                    f.write(json.dumps({'docno': doc.doc_id, 'text': doc.default_text()}) + '\n')
                    f.flush()
        
        documents = []
        with gzip.open(f'{directory}/documents.jsonl.gz', 'rt') as f:
            for l in f:
                documents += [json.loads(l)]

        indexer = pt.IterDictIndexer(os.path.abspath(f'{directory}/pyterrier-index'), meta={'docno': 100, 'text': 20480})
        index_ref = indexer.index(tqdm(documents, 'Index'))

    for retrieval_model in ['BM25', 'PL2', 'DirichletLM', 'TF_IDF', 'Hiemstra_LM']:
        index = pt.IndexFactory.of(os.path.abspath(f'{directory}/pyterrier-index'))
        output_file = f'{directory}/pyterrier-{retrieval_model}-run.gz'
        if os.path.exists(output_file):
            continue
        retriever = pt.BatchRetrieve(index, wmodel=retrieval_model)
        topics = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=['title'], tokenise=True)
        results = retriever(topics)
        pt.io.write_results(results, output_file)

    for retrieval_model, reranker in tqdm(all_re_rankers(), 'Re-Rankers'):
        for query_type in ['title', 'description']:
            output_file = f'{directory}/neural-{retrieval_model}-on{query_type}-run.gz'
            if os.path.exists(output_file):
                continue

            documents = {}
            with gzip.open(f'{directory}/documents.jsonl.gz', 'rt') as f:
                for l in f:
                    l = json.loads(l)
                    documents[l['docno']] = l['text']


            def add_text(df):
                df['text'] = df['docno'].apply(lambda i: documents[i])
                return df

            topics = pt.io.read_topics(f'{directory}/topics.xml', 'trecxml', tags=[query_type], tokenise=False)
            first_stage = pt.io.read_results(f'{directory}/pyterrier-BM25-run.gz')
            first_stage = pt.transformer.get_transformer(first_stage)
            first_stage = first_stage >> pt.apply.generic(add_text) >> reranker()

            results = first_stage(topics)
            pt.io.write_results(results, output_file)

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

        if len(docs_for_query) == 0 and len(relevant_docnos) != 0:
            print('Missing relevant docs for topic', relevant_docnos)

if __name__ == '__main__':
    main()

