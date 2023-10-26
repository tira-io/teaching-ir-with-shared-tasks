
```
docker run --rm -ti -v ${PWD}/tirex-data:/foo mam10eks/ir-datasets-wise-2023:0.0.1 --ir_datasets_id longeval-tutors --output_dataset_truth_path /foo
```

```
docker run --rm -ti -v ${PWD}/tirex-data-jena:/foo mam10eks/ir-datasets-wise-2023:0.0.1 --ir_datasets_id longeval-tutors-jena --output_dataset_truth_path /foo
```

```
docker build -t mam10eks/ir-datasets-wise-2023:0.0.1 .
docker push mam10eks/ir-datasets-wise-2023:0.0.1
```


```
docker run --rm -ti \
	-v /mnt/ceph/tira/state/ir_datasets/:/root/.ir_datasets:ro \
	-v ${PWD}/pooling:/workspace -w /workspace \
	--entrypoint python3 \
	mam10eks/ows-long-eval-ir-datasets-integration:0.0.3 \
	add-documents-to-pool.py
