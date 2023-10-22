# Step-by-Step guide for Retrieval-Submissions to Milestone 3

Before you start this step-by-step guide for milestone 3, [please ensure that you have your dedicated retrieval dataset from milestone 02](../milestone-02/README.md) in a directory `iranthology-dataset-tira`.

If you are not happy with the data format that you have choosen for your own dataset, you can use our format. In that case, please submit against the dataset `iranthology-tutors` in TIRA and you can download the dataset via:

```
wget https://files.webis.de/teaching/ir-ss23/iranthology-dataset-tutors-tira.zip
unzip iranthology-dataset-tutors-tira.zip
mv iranthology-dataset-tutors-tira iranthology-dataset-tira
```

# Step 1: Create and Evaluate Retrieval Systems Locally

We will create a docker image that contains multiple retrieval approaches.
We will then evaluate them locally, to make the retrieval system more effective than the baseline (this will be an iterative process).

The Docker image contains examples for those retrieval approaches:
- [pyterrier-bm25.ipynb](pyterrier-bm25.ipynb) The retrieval baseline upon which we want to improve.
- [pyterrier-bm25-rm3.ipynb](pyterrier-bm25-rm3.ipynb) A retrieval approach that uses RM3 to expand the query.
- [pyterrier-bm25-sdm.ipynb](pyterrier-bm25-sdm.ipynb) A retrieval approach that uses SDM to rewrite the query.
- [pyterrier-multi-field.ipynb](pyterrier-multi-field.ipynb) A retrieval approach that combines multiple retrieval scores of multiple text fields of a document. (This notebook assumes that certain fields are available in the documents. I.e., this might not work on your dataset, but works on the [dataset of the tutors](https://files.webis.de/teaching/ir-ss23/iranthology-dataset-tutors-tira.zip) you can adjust the notebook so that it works on your dataset.)

To build the docker image with the notebooks, please execute:

```
docker build -t ir-lab-milestone-03 .
```


After building the image was succesful, we can start a Jupyter notebook to develop our retrieval pipelines:

```
docker run --rm -ti -p 8888:8888 -v ${PWD}:/workspace ir-lab-milestone-03
```

If we build the image, it already comes with the four jupyter notebooks that we linked above, so lets run them locally.


# Step 2: Test your retrieval approach locally

The image that we have created already has a script `/workspace/run-pyterrier-notebook.py` embedded (see the [source if you want more information](https://github.com/tira-io/ir-experiment-platform/blob/main/tira-ir-starters/pyterrier/run-pyterrier-notebook.py)).
This script takes a jupyter notebook and the input and output directory as arguments and executes the notebook by injecting the input and output.

### Run [pyterrier-bm25.ipynb](pyterrier-bm25.ipynb)

To execute the [pyterrier-bm25.ipynb](pyterrier-bm25.ipynb) notebook that we included in our docker image on your system as TIRA would execute it, the command is:

```
tira-run \
    --input-directory ${PWD}/iranthology-dataset-tira \
    --output-directory ${PWD}/bm25-output \
    --image ir-lab-milestone-03 \
    --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/pyterrier-bm25.ipynb'
```

This should yield a run like (top 3 lines with `head -3 bm25-output/run.txt`):

```
1 0 2021.ipm_journal-ir0anthology0volumeA58A1.6 1 16.708092762527492 BM25
1 0 2011.spire_conference-2011.10 2 15.699445240396184 BM25
1 0 2019.cikm_conference-2019.346 3 15.507585799713157 BM25
```

### Run [pyterrier-bm25-rm3.ipynb](pyterrier-bm25-rm3.ipynb)

To execute the [pyterrier-bm25-rm3.ipynb](pyterrier-bm25-rm3.ipynb) notebook that we included in our docker image on your system as TIRA would execute it, the command is:

```
tira-run \
    --input-directory ${PWD}/iranthology-dataset-tira \
    --output-directory ${PWD}/bm25-rm3-output \
    --image ir-lab-milestone-03 \
    --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/pyterrier-bm25-rm3.ipynb'
```

This should yield a run like (top 3 lines with `head -3 bm25-rm3-output/run.txt`):

```
1 0 2011.spire_conference-2011.10 1 20.478847382752434 BM25-RM3
1 0 2019.cikm_conference-2019.346 2 17.69871577007762 BM25-RM3
1 0 2010.cikm_conference-2010.284 3 17.479004914010822 BM25-RM3
```

### Run [pyterrier-bm25-sdm.ipynb](pyterrier-bm25-sdm.ipynb)

To execute the [pyterrier-bm25-sdm.ipynb](pyterrier-bm25-sdm.ipynb) notebook that we included in our docker image on your system as TIRA would execute it, the command is:

```
tira-run \
    --input-directory ${PWD}/iranthology-dataset-tira \
    --output-directory ${PWD}/bm25-sdm-output \
    --image ir-lab-milestone-03 \
    --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/pyterrier-bm25-sdm.ipynb'
```

This should yield a run like (top 3 lines with `head -3 bm25-sdm-output/run.txt`):

```
1 0 2021.ipm_journal-ir0anthology0volumeA58A1.6 1 16.808092762527494 BM25-SDM
1 0 2011.spire_conference-2011.10 2 15.805688438135178 BM25-SDM
1 0 2019.cikm_conference-2019.346 3 15.560707398582654 BM25-SDM
```

### Run [pyterrier-multi-field.ipynb](pyterrier-multi-field.ipynb)

The notebook [pyterrier-multi-field.ipynb](pyterrier-multi-field.ipynb) assumes that the documents in the dataset have multiple fields.
I.e., this might not work on your dataset, but works on the [dataset of the tutors](https://files.webis.de/teaching/ir-ss23/iranthology-dataset-tutors-tira.zip) you can adjust the notebook so that it works on your dataset.

To execute the [pyterrier-multi-field.ipynb](pyterrier-multi-field.ipynb) notebook that we included in our docker image on your system as TIRA would execute it, the command is:

```
tira-run \
    --input-directory ${PWD}/iranthology-dataset-tira \
    --output-directory ${PWD}/multi-field-output \
    --image ir-lab-milestone-03 \
    --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/pyterrier-multi-field.ipynb'
```

This should yield a run like (top 3 lines with `head -3 multi-field-output/run.txt`):

```
1 0 2010.cikm_conference-2010.284 1 41.0567764391176 multi-field
1 0 2018.wwwconf_conference-2018.13 2 39.37674403947608 multi-field
1 0 2015.tist_journal-ir0anthology0volumeA6A4.12 3 37.81074710961472 multi-field
```

## Evaluate and render your runs

Please note that you can render and evaluate all runs [as shown in the end of milestone 2](../milestone-02/README.md) to develop and improve your retrieval system. You can play around with different approaches and test ideas and see if they work by evaluating them as you did in the end of milestone 2.


# Step 3: Submit tested retrieval approaches to TIRA

First, ensure that you are authenticated to your dedicated registry (via `docker login`, detailed instructions on how to access your credentials can be found [here](https://www.tira.io/t/how-to-make-a-software-submission-with-docker/1437)).

Second, please upload the docker image to your dedicated registry:

```
docker tag ir-lab-milestone-02 registry.webis.de/code-research/tira/tira-user-ir-lab-sose-2023-<YOUR-GROUP-NANME>/milestone-03:0.0.1
docker push registry.webis.de/code-research/tira/tira-user-ir-lab-sose-2023-<YOUR-GROUP-NANME>/milestone-03:0.0.1
```

In TIRA, click on "Docker Submission" -> "Add Container" and specify the docker image and the to-be-executed command.
E.g., for the `pyterrier-bm25.ipynb` notebook, the output form should look like this:

![Screenshot_20230502_200700](https://user-images.githubusercontent.com/10050886/235749533-d710cf36-c097-4c23-96de-56d746073ca8.png)

After you have added the software, you can run it by specifying the dataset on which it should run (your dataset created for milestone 1 or iranthology-tutors) and the resources that it gets for its execution:

![Screenshot_20230502_201037](https://user-images.githubusercontent.com/10050886/235749854-262de14a-16ee-4d1e-9fb4-61fd90a943dd.png)

Thats it, you can repeat this cycle as long as you want and submit as many submissions as you like :)

