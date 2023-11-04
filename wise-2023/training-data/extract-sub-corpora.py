#!/usr/bin/env python3
import ir_datasets

datasets = {'training': 'longeval/train', 'heldout': 'longeval/train', 'short-july': 'longeval/a-short-july', 'long-september': 'longeval/b-long-september'}
#data = ir_datasets.load()

if __name__ == '__main__':
    for k, v in dataset.items():
        print(f'{k} -> {v}')

