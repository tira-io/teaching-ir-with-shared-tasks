#!/usr/bin/bash

docker run --rm -v /mnt/ceph/tira/state/ir_datasets:/root/.ir_datasets:ro -v ${PWD}:/foo -w /foo -ti --entrypoint python3 mam10eks/ows-long-eval-ir-datasets-integration:0.0.3 extract-sub-corpora.py
