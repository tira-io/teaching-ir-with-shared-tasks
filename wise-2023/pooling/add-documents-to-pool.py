import ir_datasets
import json
from tqdm import tqdm

data = ir_datasets.load('longeval/train')
docs_store = data.docs_store()
#print(docs_store.get('doc062201000001'))

for dataset in ['leipzig-topics-20231025-test', 'jena-topics-20231026-test']:
    data = json.load(open(f'{dataset}-pool.json', 'r'))
    for topic in data.keys():
        docs = [docs_store.get(i) for i in tqdm(data[topic]['pool'])]
        data[topic]['pool_wit_docs'] = [{'doc_id': i.doc_id, 'text': i.default_text()} for i in docs]
    
    json.dump(data, open(f'{dataset}-pool-with-docs.json', 'w'))

