#!/usr/bin/env python3
from trectools import TrecPoolMaker, TrecRun
from tira.rest_api_client import Client
import json
import pandas as pd

tira = Client()

topics = {}
tmp = pd.read_json('../ir-datasets/tirex-data/queries.jsonl', lines=True)
tmp = {i['original_query']['query_id']: i['original_query'] for _, i in tmp.iterrows()}

topics['leipzig-topics-20231025-test'] = tmp

tmp = pd.read_json('../ir-datasets/tirex-data-jena/queries.jsonl', lines=True)
tmp = {i['original_query']['query_id']: i['original_query'] for _, i in tmp.iterrows()}

topics['jena-topics-20231026-test'] = tmp


for dataset in ['leipzig-topics-20231025-test']:
    runs = []
    for approach in ['TF-IDF', 'DFIC', 'DirichletLM', 'DLH', 'DPH', 'BM25', 'IFB2', 'HiemstraLM', 'PL2', 'LGD']:
        run = tira.get_run_output(f'ir-lab-jena-leipzig-wise-2023/ir-lab-sose-2023-tutors/{approach}', dataset, True)
        runs += [TrecRun(run +'/run.txt')]
    pool = TrecPoolMaker().make_pool(runs, strategy="topX", topX=25)
    print(pool)
    with open(f'{dataset}-pool.json', 'w') as f:
        pool = {k: {'pool': list(v)} for k, v in pool.pool.items()}
        for k in pool.keys():
            pool[k]['topic'] = topics[dataset][k]
        
        f.write(json.dumps(pool))
