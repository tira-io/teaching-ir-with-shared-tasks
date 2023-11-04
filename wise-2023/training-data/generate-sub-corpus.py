#!/usr/bin/env python3
import pandas as pd
import json

def load_docs_from_qrels(f):
    return list(pd.read_csv(f'qrels-{f}.txt', names=['qid', 'q0', 'docno', 'rel'], sep='\s+')['docno'].unique())

def load_run(f):
    ret = pd.read_csv(f'run-ows-bm25-{f}.gz', sep='\s+', names=['qid', 'q0', 'docno', 'rank', 'score', 'system'])
    ret = ret[ret['rank'] <= 100]
    return list(ret['docno'].unique())

def main(f):
    print(f)
    ret = set(load_docs_from_qrels(f) + load_run(f))
    print(f)
    with open(f'docs-{f}.json', 'w+') as f:
        f.write(json.dumps(list(ret)))

if __name__ == '__main__':
    main('training')
    main('heldout')
    main('short-july')
    main('long-september')

