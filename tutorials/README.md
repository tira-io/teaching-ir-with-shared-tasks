# Tutorials for the IR Lab in WiSe 2023

This directory contains the tutorials that we will use in the IR lab in WiSe 2023.

We recommend that you run this tutorials using dev containers with Docker (please find a suitable installation instruction [here](https://code.visualstudio.com/docs/devcontainers/containers)).
A dev container allows you to directly work in the prepared Docker container so that you do not have to install the dependencies (which can sometimes be a bit tricky) on your own. If you do not have Docker installed (we highly recommend that you have a look into Docker), you can run everything within Google Colab.

To run the tutorials on your machine, please:

- Install [VS Code](https://code.visualstudio.com/download) and [Docker](https://docs.docker.com/engine/install/) on your machine
- Clone this repository: `git clone ...`
- Open this directory with VS Code (it should ask you to open the repository in a dev container)


### Content

For tutors: The tutor repository contains a directory [sample-solutions](sample-solutions) with all solutions.

- [Tutorial 1: Topics, Documents, and Relevance Judgments](tutorial-01-ir-datasets.ipynb) (Open in [GitHub](tutorial-01-ir-datasets.ipynb) or [Google Colab](https://colab.research.google.com/drive/1oWh9nFT6ZsGfZLRDG1QrwUgyMIzLbw_H?usp=sharing))
- [Tutorial 2: Stopword Lists](tutorial-02-stopword-lists.ipynb) (Open in [GitHub](tutorial-02-stopword-lists.ipynb) or ToDo Add Google Colab)
- [Tutorial 3 (in progress by Maik): Stemming](tutorial-03-stemming.ipynb) (Open in [GitHub](tutorial-03-stemming.ipynb) or ToDo Add Google Colab)
- [Tutorial 4 (in progress by Maik): Lemmatization](tutorial-04-lemmatization.ipynb) (Open in [GitHub](tutorial-04-lemmatization.ipynb) or ToDo Add Google Colab)
- [Tutorial 5: Query Expansion](tutorial-05-query-expansion.ipynb) (Open in [GitHub](tutorial-05-query-expansion.ipynb) or ToDo Add Google Colab)
- Tutorial 8: Query Segmentation (In progress by Maik)
- [Tutorial 9 (research oriented): Query Expansion with LLMs](tutorial-09-query-expansion-with-llms.ipynb) (Open in [GitHub](tutorial-09-query-expansion-with-llms.ipynb) or ToDo Add Google Colab)

### Changes to the Dev-Container

We are happy if you find ways to improve the dev container. You can adjust the image as you like, if you think your changes might be helpful to others, please let us know so that we can adjust the published image.

Instructions to build and publish the image are:

```
docker build -t webis/ir-lab-wise-2023:0.0.1 .
docker push webis/ir-lab-wise-2023:0.0.1
```

