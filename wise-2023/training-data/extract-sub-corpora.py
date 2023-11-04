#!/usr/bin/env python3
import ir_datasets
import json
from tqdm import tqdm
import gzip

datasets = {'training': 'longeval/train', 'heldout': 'longeval/train', 'short-july': 'longeval/a-short-july', 'long-september': 'longeval/b-long-september'}

def main(k, v):
    docs_store = ir_datasets.load(v).docs_store()
    doc_ids = json.load(open(f'docs-{f}.json', 'r'))
    with gzip.open(f'{f}/documents.jsonl.gz', 'wt') as f:
        for doc_id in tqdm(doc_ids):
            doc = docs_store.get(doc_id)
            f.write(json.dumps({"docno": doc_id, "text": doc.default_text()}) + '\n')

if __name__ == '__main__':
    for k, v in datasets.items():
        print(f'{k} -> {v}')

