#!/usr/bin/env python3
from trectools import TrecPoolMaker, TrecRun
from tira.rest_api_client import Client
import json

tira = Client()


for dataset in ['leipzig-topics-20231025-test']:
    runs = []
    for approach in ['TF-IDF', 'DFIC', 'DirichletLM', 'DLH', 'DPH', 'BM25', 'IFB2', 'HiemstraLM', 'PL2', 'LGD']:
        run = tira.get_run_output(f'ir-lab-jena-leipzig-wise-2023/ir-lab-sose-2023-tutors/{approach}', dataset, True)
        runs += [TrecRun(run +'/run.txt')]
    pool = TrecPoolMaker().make_pool(runs, strategy="topX", topX=25)
    print(pool)
    with open(f'{dataset}-pool.json', 'w') as f:
        f.write(json.dumps({k: list(v) for k, v in pool.pool.items()}))
