# Tutorials for the IR Lab in WiSe 2023

This directory contains the tutorials that we will use in the IR lab in WiSe 2023.

You can easily run those tutorials online in a [Github Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main). If you want to learn more of the technical background, we recommend that you run this tutorials using dev containers with Docker (please find a suitable installation instruction [here](https://code.visualstudio.com/docs/devcontainers/containers)).
A dev container allows you to directly work in the prepared Docker container so that you do not have to install the dependencies (which can sometimes be a bit tricky) on your own. If you do not have Docker installed (we highly recommend that you have a look into Docker), you can run everything within [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main).

To run the tutorials on your machine, please:

- Install [VS Code](https://code.visualstudio.com/download) and [Docker](https://docs.docker.com/engine/install/) on your machine
- Clone this repository: `git clone ...`
- Open this directory with VS Code (it should ask you to open the repository in a dev container)

If you do not want to use VS Code and dev containers, you can start a jupyter notebook via (please execute the command within this directory):

```
docker run --rm  -it -p 8888:8888 --entrypoint jupyter -w /workspace -v ${PWD}:/workspace webis/ir-lab-wise-2023:0.0.1 notebook --allow-root --ip 0.0.0.0
```

## Content

For tutors: The tutor repository contains a directory [sample-solutions](sample-solutions) with all solutions.
Please also have a a look at the official [PyTerrier tutorial](https://github.com/terrier-org/ecir2021tutorial).

### Tutorial 1: Topics, Documents, and Relevance Judgments
- Jupyter Notebook in [GitHub](tutorial-01-ir-datasets.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 2: Stopword Lists
- Jupyter Notebook in [GitHub](tutorial-02-stopword-lists.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 3 (in progress by Maik): Stemming
- Jupyter Notebook in [GitHub](tutorial-03-stemming.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 4 (in progress by Maik): Lemmatization
- Jupyter Notebook in [GitHub](tutorial-04-lemmatization.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 5: Query Expansion
- Jupyter Notebook in [GitHub](tutorial-05-query-expansion.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 6: Hyperparameter Tuning
- Jupyter Notebook in [GitHub](tutorial-06-hyperparameter-tuning.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 7: Query Segmentation (In progress by Maik)
- Jupyter Notebook in [GitHub](tutorial-07-query-segmentation.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 8: Query Performance Prediction (In progress by Maik)
- Jupyter Notebook in [GitHub](tutorial-08-query-performance-prediction.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Tutorial 9 (research oriented): Query Expansion with LLMs
- Jupyter Notebook in [GitHub](tutorial-09-query-expansion-with-llms.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

### Research Tutorial: Classification of Medical/Health Queries and Documents
- Jupyter Notebook in [GitHub](tutorial-research-medical-classification.ipynb)
- Open in [Codespace](https://github.com/codespaces/new/webis-de/ir-pad/tree/main)

Open:
- Query Performance Prediction: Maik 13.11.
- LTR: Maik 13.11.
- Cross-Encoder / Bi-Encoder: Heinrich 18.12
- 
### Changes to the Dev-Container

We are happy if you find ways to improve the dev container. You can adjust the image as you like, if you think your changes might be helpful to others, please let us know so that we can adjust the published image.

Instructions to build and publish the image are:

```
docker build -t webis/ir-lab-wise-2023:0.0.2 .
docker push webis/ir-lab-wise-2023:0.0.2
```

