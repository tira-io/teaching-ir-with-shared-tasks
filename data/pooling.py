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
    docs_store = ir_datasets.load('msmarco-segment-v2.1').docs_store()
    
    if not os.path.exists(f'{directory}/pyterrier-index'):
        documents = []
        if not os.path.exists(f'{directory}/documents.jsonl.gz'):
            with gzip.open(f'{directory}/documents.jsonl.gz', 'wt') as f:
                for doc in tqdm(all_docs, 'Load Docs'):
                    doc = docs_store.get(doc)
                    f.write(json.dumps({'docno': doc.doc_id, 'text': doc.default_text()}) + '\n')
                    f.flush()

        indexer = pt.IterDictIndexer(os.abspath(f'{directory}/pyterrier-index'), meta={'docno': 100, 'text': 20480})
        index_ref = indexer.index(documents)
    index = pt.IndexFactory.of(os.abspath(f'{directory}/pyterrier-index'))


    for _, t in tqdm(list(relevant_documents_per_topic.iterrows()), 'Expansion Docs'):
        docs_for_query = set()
        relevant_docnos = t['query'].split(',')
        for relevant_doc in relevant_docnos:
            for doc in all_docs:
                if doc.startswith(relevant_doc + '#'):
                    docs_for_query.add(doc)
        print(len(docs_for_query))
    
if __name__ == '__main__':
    main()

