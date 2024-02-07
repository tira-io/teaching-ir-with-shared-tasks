# Zenodo Artifacts for Teaching IR with Shared Tasks

This is intended as a blueprint directory for uploading the data artifacts  to [Zenodo](https://zenodo.org/) to allow for scalable and reliable access to the datasets (Zenodo is intended to provide trusted and save [data access over the coming 20 years](https://help.zenodo.org/faq/)) making the data available.

## Already Published Artifacts

The course concept was previously executed in [summer term 2023](https://tira-io.github.io/ir-lab-sose-23/) and [winter term 2023/2024](https://tira-io.github.io/ir-lab-ws-23/) with the corresponding Zenodo Artifacts described below.

### Resources of the Summer Term 2023

> TODO

### Resources of the Winter Term 2023

> TODO

# The Datasets for the Information Retrieval Course at <UNIVERSITIES_HERE> in <YEAR>

This repository contains resources coupled to [ir_datasets](https://arxiv.org/pdf/2103.02280.pdf) and [TIREx](https://webis.de/publications.html?q=tira#froebe_2023e) for IR courses that focus their hands-on labs on shared tasks. During the IR exercises in <YEAR>, we collaboratively developed and evaluated IR systems in a shared task style setup, covering corpus creation, system development, and statistical analysis. The resulting artifacts, i.e., the documents, topics, runs, relevance judgments can be browsed at <URL>. This zenodo artifact contains all of the underlying datasets used and produced during the course together with instructions on how to easily access the data using ir_datasets.

## Overview of resources

This dataset contains the resources used and created during the IR course at [TODO Link].

The artifact contains the following files:

- training-inputs.zip containing the training inputs to systems, i.e., containing the document corpus and the topics.
- training-truths.zip containing the training truth to evaluate and tune systems, i.e., the topics and relevance judgments.
- validation-inputs.zip containing the validation inputs to systems, i.e., containing the document corpus and the topics.
- validation-truths.zip containing the validation truth to evaluate and tune systems, i.e., the topics and relevance judgments.

## Accessing the Data with ir_datasets

We provide wrapper code to easily access the resources with ir_datasets:

```
# this loads a patched version of ir_datasets that can load resources from TIRA
from tira.third_party_integrations import ir_datasets


training_dataset = 'ir-lab-jena-leipzig-wise-2023/training-20231104-training'
validation_dataset = 'ir-lab-jena-leipzig-wise-2023/validation-20231104-training'
```

Similarly, the same is possible with the ir_datasets integration to PyTerrier:

```
from tira.third_party_integrations import ensure_pyterrier_is_loaded
import pyterrier as pt

# this patches ir_datasets and loads PyTerrier so that it can load resources from TIRA and can run in the TIRA sandbox
ensure_pyterrier_is_loaded()

training_dataset = pt.datasets.get_dataset('irds:ir-lab-jena-leipzig-wise-2023/training-20231104-training')
validation_dataset = pt.datasets.get_dataset('irds:ir-lab-jena-leipzig-wise-2023/validation-20231104-training')
```

## Future Maintenance and Versioning of Data Artifacts on Zenodo

Zenodo supports versioning of datasets.
Therefore, the intended workflow to cover all four milestones of the course concept is to create the following versions throughout the course:

### Step 1: Prepare the data to support milestones 2 and 3

Before milestone 1 starts: upload a first version of the dataset the public training dataset:
  - training-inputs.zip containing the training inputs to systems, i.e., containing the document corpus and the topics.
  - training-truths.zip containing the training truth to evaluate and tune systems, i.e., the topics and relevance judgments.
  - validation-inputs.zip containing the validation inputs to systems, i.e., containing the document corpus and the topics.
  - validation-truths.zip containing the validation truth to evaluate and tune systems, i.e., the topics and relevance judgments.

### Step 2: Prepare the data to support milestones 2 and 3

- Step 2 (After milestone 3 before milestone 4): Upload the corpus created during the course and all runs that were submitted, i.e.,
  - test-<university>-inputs.zip containing the test inputs constructed at the given university, i.e., containing the document corpus and the topics.
  - test-<university>-truths.zip containing the test truth to evaluate systems used for statistical analysis, i.e., the topics and relevance judgments.
  - run-<group-id>-<dataset-id>-<run-id>.zip: pattern for all runs.
