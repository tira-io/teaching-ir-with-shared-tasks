# Tutorials for the IR Lab in WiSe 2023

This directory contains the tutorials that we will use in the IR lab in WiSe 2023.

We recommend that you run this tutorials using dev containers with Docker (please find a suitable installation instruction [here](https://code.visualstudio.com/docs/devcontainers/containers)).
A dev container allows you to directly work in the prepared Docker container so that you do not have to install the dependencies (which can sometimes be a bit tricky) on your own. If you do not have Docker installed (we highly recommend that you have a look into Docker), you can run everything within Google Colab.

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
- Open in [Google Colab](https://colab.research.google.com/drive/1oWh9nFT6ZsGfZLRDG1QrwUgyMIzLbw_H?usp=sharing)

### Tutorial 2: Stopword Lists
- Jupyter Notebook in [GitHub](tutorial-02-stopword-lists.ipynb)
- ToDo Add Google Colab

### Tutorial 3 (in progress by Maik): Stemming
- Jupyter Notebook in [GitHub](tutorial-03-stemming.ipynb)
- ToDo Add Google Colab

### Tutorial 4 (in progress by Maik): Lemmatization
- Jupyter Notebook in [GitHub](tutorial-04-lemmatization.ipynb)
- ToDo Add Google Colab

### Tutorial 5: Query Expansion
- Jupyter Notebook in [GitHub](tutorial-05-query-expansion.ipynb)
- ToDo Add Google Colab

### Tutorial 6: Hyperparameter Tuning
- Jupyter Notebook in [GitHub](tutorial-06-hyperparameter-tuning.ipynb)
- Open in [Google Colab](https://colab.research.google.com/drive/1rEMHslBKKiSmWRRhzjtMG2jIN2vilt3T?usp=sharing)

### Tutorial 8: Query Segmentation (In progress by Maik)
- Jupyter Notebook in [GitHub](tutorial-07-query-segmentation.ipynb)
- ToDo Add Google Colab

### Tutorial 9 (research oriented): Query Expansion with LLMs
- Jupyter Notebook in [GitHub](tutorial-09-query-expansion-with-llms.ipynb)
- ToDo Add Google Colab

### Research Tutorial: Classification of Medical/Health Queries and Documents
- Jupyter Notebook in [GitHub](tutorial-research-medical-classification.ipynb)
- Todo Add Google Colab

Open:
- Grid Search with Trectools, etc: Lukas 30.10.
- Query Performance Prediction: Maik 13.11.
- LTR: Maik 13.11.
- Cross-Encoder / Bi-Encoder: Heinrich 18.12
- 
### Changes to the Dev-Container

We are happy if you find ways to improve the dev container. You can adjust the image as you like, if you think your changes might be helpful to others, please let us know so that we can adjust the published image.

Instructions to build and publish the image are:

```
docker build -t webis/ir-lab-wise-2023:0.0.1 .
docker push webis/ir-lab-wise-2023:0.0.1
```

