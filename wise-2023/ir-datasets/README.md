
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
