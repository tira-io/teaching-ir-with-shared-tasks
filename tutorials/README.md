# Tutorials

Hands-on tutorials to kick-start the development and evaluation of information retrieval systems.

In this directory, we provide plenty Jupyter notebooks that guide students through specific aspects of information retrieval experimentation starting from [data exploration](tutorial-ir-datasets.ipynb) over [simple retrieval approaches](tutorial-query-expansion.ipynb) to [statistical analysis](tutorial-statistical-analysis.ipynb).

The fastest and easiest way to run our tutorials is to use Github Codespaces. Just click on the button below which will start a remote session with everything installed already:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1)

## Recommendet Order of Tutorials:

The tutorials cover diverse contents, we recommend that you start with basic tutorials:

1. The [https://github.com/terrier-org/ecir2021tutorial?tab=readme-ov-file#contents](PyTerrier Tutorial), in particular [Part 1](https://github.com/terrier-org/ecir2021tutorial/blob/main/slides/part1.pdf) and [Part 2](https://github.com/terrier-org/ecir2021tutorial/blob/main/slides/part2.pdf).
2. The [tutorial-ir-datasets.ipynb](tutorial-ir-datasets.ipynb)

After this, you can go towards the more advanced tutorials: [tutorial-stopword-lists.ipynb](tutorial-stopword-lists.ipynb), [tutorial-stemming.ipynb](tutorial-stemming.ipynb), [tutorial-lemmatization.ipynb](tutorial-lemmatization.ipynb), [tutorial-query-expansion.ipynb](tutorial-query-expansion.ipynb), and the [tutorial-statistical-analysis.ipynb](tutorial-statistical-analysis.ipynb).

After you completed them, you can also visit the more research oriented tutorials in this directory or in the PyTerrier Tutorial (e.g., Part 3 and 4).

## Contents

Our basic tutorials cover the most important concepts of information retrieval and are broken down based on very simple, easy-to-understand examples. The entry-level tutorials are targeted to Bachelor's (or early Master's) students:

| Topic | Jupyter Notebook | Open in Codespaces |
|:--|:-:|:-:|
| Topics, documents, and relevance judgments | [🔗](tutorial-ir-datasets.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-ir-datasets.ipynb?quickstart=1) |
| Stopword lists | [🔗](tutorial-stopword-lists.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-stopword-lists.ipynb?quickstart=1) |
| Stemming | [🔗](tutorial-stemming.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-stemming.ipynb?quickstart=1) |
| Lemmatization | [🔗](tutorial-lemmatization.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-lemmatization.ipynb?quickstart=1) |
| Query expansion | [🔗](tutorial-query-expansion.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-query-expansion.ipynb?quickstart=1) |
| Hyperparameter tuning | [🔗](tutorial-hyperparameter-tuning.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-hyperparameter-tuning.ipynb?quickstart=1) |
| Statistical analysis | [🔗](tutorial-statistical-analysis.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-statistical-analysis.ipynb?quickstart=1) |
| Learning to rank ([work in progress](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/2)) | [⏳](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/2) | [⏳](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/2) |
| _Anyhting missing? [Propose new tutorial.](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/new)_ | | |

More complex topics that might not be suited to every IR course are still covered in our research-oriented tutorials. These tutorials are often more complex and require more prior knowledge, so they are best suited for Master's students:

| Topic | Jupyter Notebook | Open in Codespaces |
|:--|:-:|:-:|
| Query expansion with LLMs | [🔗](tutorial-query-expansion-with-llms.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-query-expansion-with-llms.ipynb?quickstart=1) |
| Query segmentation | [🔗](tutorial-query-segmentation.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-query-segmentation.ipynb?quickstart=1) |
| Query performance prediction | [🔗](tutorial-query-performance-prediction.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-query-performance-prediction.ipynb?quickstart=1) |
| Classification of medical/health queries and documents | [🔗](tutorial-medical-classification.ipynb) | [💻](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks/tree/main/tutorials/tutorial-medical-classification.ipynb?quickstart=1) |
| Entity linking ([work in progress](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/4)) |  [🔗](tutorial-entity-linking-in-progress.ipynb) | [⏳](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/4) |
| Query Intent Prediction (work in progress)|  [🔗](tutorial-query-intent-prediction.ipynb) | ⏳ |
| Query Spelling Correction (work in progress)|  [🔗](tutorial-spelling-correction.ipynb) | ⏳ |
| Splade for Query Processing (work in progress)|  [🔗](tutorial-splade-query-processing.ipynb) | ⏳ |
| Splade for Document Processing (work in progress)|  [🔗](tutorial-splade-ranking.ipynb) | ⏳ |
| DocT5Query (work in progress)|  [🔗](tutorial-doc-t5-query.ipynb) | ⏳ |
| Genre Classification (work in progress)|  [🔗](tutorial-genre-classification.ipynb) | ⏳ |
| Corpus Graph (work in progress)|  [🔗](tutorial-corpus-graph.ipynb) | ⏳ |
| Re-ranking with cross-encoders or bi-encoders ([work in progress](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/3)) | [⏳](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/3) | [⏳](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/3) |
| _Anyhting missing? [Propose new tutorial.](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/new)_ | | |

Of course, this list can never be exhaustive, as paradigms shift and technologies change.
However, we are very happy about any contribution from the open science community!
For example, you could [request a tutorial](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/new) for a certain topic or [submit a pull request](https://github.com/tira-io/teaching-ir-with-shared-tasks/compare) where you add it yourself.

## Local usage

This repository and the tutorials within are designed to be run and developed inside [Dev containers](https://containers.dev/). Though the easiest way to run Dev containers is to just [spin up a GitHub Codespace](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1), you can also run everything on your local machine with Visual Studio Code and Docker ([installation instructions](https://code.visualstudio.com/docs/devcontainers/containers#_installation)). (Some [other IDEs](https://containers.dev/supporting) might also work.) Even locally, our Dev container allows you to directly start coding without having to install dependencies on your own. To run the tutorials on your machine, follow these steps:

- Install [Visual Studio Code](https://code.visualstudio.com/download) and [Docker](https://docker.com/get-started/).
- Clone this repository (`git clone`)
- Open the cloned directory in Visual Studio Code
- Once asked (VS Code popup), re-open the directory in a Dev container

As another alternative, you could start up a Jupyter server to edit a notebook with Docker (run the command within the cloned directory):

```shell
docker run --rm  -it -p 8888:8888 --entrypoint jupyter -w /workspace -v ${PWD}:/workspace webis/ir-lab-wise-2023 notebook --allow-root --ip 0.0.0.0
```

## Contributing

With the plethora of new retrieval approaches emerging every year, it is hard for us alone to update and add all new tutorials. We are grateful for any IR teacher who invests some time to contribute back to our free teaching resources!

To do so, just [open this repository in GitHub Codespaces](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1) (or clone it and open the repo in a [Dev container](https://containers.dev/) with your [favorite IDE](https://containers.dev/supporting)).

Feel free to locally adapt the base image (`webis/ir-lab-wise-2023:0.0.3`) to your liking. If you think your changes might be helpful to others as well, please [let us know](#contact) so that we can adjust the public image.

Staff can build and publish the image like this (replace `X.Y.Z` with the actual version):

```shell
docker build -t webis/ir-lab-wise-2023:X.Y.Z .
docker push webis/ir-lab-wise-2023:X.Y.Z
```

## Contact

We would be glad to support you in running our tutorials!
Do not hesitate to write us an email or file an [issue](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/new):

- Maik Fröbe [maik.froebe@uni-jena.de](mailto:maik.froebe@uni-jena.de)
- Harrisen Scells
- Theresa Elstner
- Christopher Akiki
- Lukas Gienapp
- Jan Heinrich Merker [heinrich.merker@uni-jena.de](mailto:heinrich.merker@uni-jena.de)
- Sean MacAvaney
- Benno Stein
- Matthias Hagen
- Martin Potthast

We're happy to help!

## Similar resources

We took inspiration from some great tutorials and resources out there. Of course, our resources should not replace but complement them:

- [The PyTerrier Tutorial](https://github.com/terrier-org/ecir2021tutorial)

## License

Please refer to the [root readme](../README.md).
