<!-- [![Paper DOI](https://img.shields.io/badge/DOI-10.1145%2F3477495.3531743-blue?style=flat-square)](https://doi.org/10.1145/3477495.3531743) -->
<!-- [![arXiv preprint](https://img.shields.io/badge/arXiv-2304.00413-blue?style=flat-square)](https://arxiv.org/abs/2304.00413) -->
<!-- [![CI status](https://img.shields.io/github/actions/workflow/status/tira-io/teaching-ir-with-shared-tasks/ci.yml?branch=main&style=flat-square)](https://github.com/tira-io/teaching-ir-with-shared-tasks/actions/workflows/ci.yml) -->
[![Issues](https://img.shields.io/github/issues/tira-io/teaching-ir-with-shared-tasks?style=flat-square)](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/tira-io/teaching-ir-with-shared-tasks?style=flat-square)](https://github.com/tira-io/teaching-ir-with-shared-tasks/pulls)
[![Commit activity](https://img.shields.io/github/commit-activity/m/tira-io/teaching-ir-with-shared-tasks?style=flat-square)](https://github.com/tira-io/teaching-ir-with-shared-tasks/commits)
[![Maintenance](https://img.shields.io/maintenance/yes/2024?style=flat-square)](https://github.com/tira-io/teaching-ir-with-shared-tasks/graphs/contributors)
[![License](https://img.shields.io/github/license/tira-io/teaching-ir-with-shared-tasks?style=flat-square)](LICENSE)

# 🧪 Teaching IR with Shared Tasks

Resources for combining teaching and research in information retrieval coursework.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1)

The resources are intended as a collection of supplementary materials for exercises in IR courses that let students experience the full research cycle in their course. We provide:

- A [dashboard](#dashboard) to support brainstorming
  - Explore datasets, approaches, and evaluation techniques
  - Easy to use [online](https://tira-io.github.io/teaching-ir-with-shared-tasks/)
  - Links to in-depth resources
- An [`ir_datasets` browser](#ir_datasets-browser) to explore datasets and runs from TIREx
  - Reuse and explore strong baselines from [TIREx](https://tira.io/tirex)
  - Deep links for referencing in research papers
  - Hosted on GitHub Pages and Zenodo
- A set of [tutorials](#tutorials) covering IR concepts
  - Showcases a single concept using small example data
  - Takes about 15 minutes per tutorial
  - Implemented as Jupyter notebooks in [GitHub Codespaces](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1)
- A way to [archive finished courses](#archived-courses)
  - Explore topics, documents, relevance judgments, and submitted runs
  - Leaderboards encourage competition between students
  - Course results are easily re-usable for research

Read more about the resources in our accompanying research paper: \
Resources for Combining Teaching and Research in Information Retrieval Coursework
<!-- [Resources for Combining Teaching and Research in Information Retrieval Coursework](TODO) ([abstract](#abstract)) -->

## Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Dashboard](#dashboard)
  - [`ir_datasets` browser](#ir_datasets-browser)
  - [Tutorials](#tutorials)
  - [Archived courses](#archived-courses)
- [Testimonials](#testimonials)
- [Contributing](#contributing)
- [Contact/License/Abstract](#contact)

## Screencasts

Please find an short screencast [showing our resources on youtube](https://youtu.be/JvbiPoyjZoc).

## Installation

The easiest way to start with the tutorials is to open this repository in GitHub Codespaces: \
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1) \
This will install all the necessary software. Just wait until the editor window has fully loaded (i.e., no progress bars visible; may take a while). \
The other resources (i.e., [dashboard](#dashboard), [`ir_datasets` browser](#ir_datasets-browser), and [archived courses](#archived-courses)) are static web apps that you can run in your web browser.

## Usage

In the following, you will learn how to use each of the four main components of our resources:
the [dashboard](#dashboard), the [`ir_datasets` browser](#ir_datasets-browser), the [tutorials](#tutorials), and the [archived courses](#archived-courses).
The sections roughly follow the order as you would use the components in your course (either as a student or teacher).

### Dashboard

Check out the dashboard web app at: <https://tira-io.github.io/teaching-ir-with-shared-tasks>

![Dashboard web app](docs/screenshot-dashboard.png)

Explore existing datasets, retrieval components, and evaluation measures with deep links to implementations and papers.
Components can be filtered to only include, e.g., components with code available or with a corresponding [tutorial](#tutorials).
To focus your search on a specific goal, e.g., precision-oriented components, select a research focus from the dropdown list.

### `ir_datasets` browser

The `ir_datasets` browser can be used to explore existing datasets: <https://tira-io.github.io/ir-dataset-browser>

![`ir_datasets` browser web app](docs/screenshot-ir-datasets-browser.png)

Here are some examples that can be found using the browser:

- [Topic with high nDCG@10 variange](https://tira-io.github.io/ir-dataset-browser/topics?topic=962179&dataset=msmarco-passage/trec-dl-2019/judged)
- [Topic with low nDCG@10 variance](https://tira-io.github.io/ir-dataset-browser/topics?topic=131843&dataset=msmarco-passage/trec-dl-2019/judged)
- [Browsing a document](https://tira-io.github.io/ir-dataset-browser/docs?dataset=msmarco-passage/trec-dl-2019/judged&doc_ids=7501563)

A total of 13 datasets are already available to be explored online. (Some others could not be included due to their licenses.)

### Tutorials

Our hands-on tutorials lower the barrier of entry to implementing IR models and experiments for IR students. You can easily run the tutorials online:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1)

A full list of all covered tutorials and further information on how to run the tutorials on your local machine can be found in the [tutorial readme](tutorials/README.md).

## Archived courses

The below list includes finished (✅), ongoing (⏳) and future (🔜) IR courses that already benefit from our teaching resources.
The finished courses have been archived on Zenodo and are accessible via GitHub Pages. To explore their topics and relevance judgments, click on the "browser" links.
[Get in touch](#contact) to integrate your course too!

| 📅 | Semester | Course | University | Browser | Source |
|:-:|:--|:--|:--|:-:|:-:|
| ✅ | Summer semester 2023 | [Information Retrieval](https://temir.org/teaching/information-retrieval-ss23/information-retrieval-ss23.html) | [Leipzig University](https://leipzig.webis.de) | [🔗](https://tira-io.github.io/ir-lab-sose-23/) | [🔗](https://github.com/tira-io/ir-lab-sose-23) |
| ✅ | Summer semester 2023 | Advanced Information Retrieval |  [Friedrich-Schiller-Universität Jena](https://jena.webis.de) | [🔗](https://tira-io.github.io/ir-lab-sose-23/) | [🔗](https://github.com/tira-io/ir-lab-sose-23) |
| ✅ | Winter semester 2023/2024 | [Advanced Information Retrieval](https://temir.org/teaching/information-retrieval-ws23/information-retrieval-ws23.html) | [Leipzig University](https://leipzig.webis.de) | [🔗](https://tira-io.github.io/ir-lab-ws-23/) | [🔗](https://github.com/tira-io/ir-lab-ws-23) |
| ✅ | Winter semester 2023/2024 | Information Retrieval | [Friedrich-Schiller-Universität Jena](https://jena.webis.de) | [🔗](https://tira-io.github.io/ir-lab-ws-23/) | [🔗](https://github.com/tira-io/ir-lab-ws-23) |
| ⏳ | Summer semester 2024 | Advanced Information Retrieval |[Friedrich-Schiller-Universität Jena](https://jena.webis.de) | ⏳ | ⏳ |
| 🔜 | _soon_ | _**your** IR course_ | _[get in touch 💬](#contact)_ | 🔜 | 🔜 |

<!-- Our accompanying [research paper](#citation) includes a case study and describes our experiences of using our resources in the IR courses of two universities over two semesters. -->

## Similar resources

We took inspiration from some great tutorials and resources out there. Of course, our resources should not replace but complement them:

- [The PyTerrier Tutorial](https://github.com/terrier-org/ecir2021tutorial)

## Contributing

With the plethora of new retrieval approaches emerging every year, it is hard for us alone to keep all resources up-to-date and to add new tutorials. We would be extremely happy if you (as an IR teacher) could take some time to improve an existing notebook or propose a new one!

Contributing to the resources is as easy as using it: Just [open this repository in GitHub Codespaces](https://github.com/codespaces/new/tira-io/teaching-ir-with-shared-tasks?quickstart=1) (or clone it and open the repo in a [Dev container](https://containers.dev/) with your [favorite IDE](https://containers.dev/supporting)).

## Contact

We would be glad to support you in applying shared task style teaching for your information retrieval course!
Do not hesitate to write us an email or file an [issue](https://github.com/tira-io/teaching-ir-with-shared-tasks/issues/new):

- Maik Fröbe [maik.froebe@uni-jena.de](mailto:maik.froebe@uni-jena.de)
- Harrisen Scells
- Theresa Elstner
- Christopher Akiki
- Lukas Gienapp
- Jan Heinrich Reimer [heinrich.reimer@uni-jena.de](mailto:heinrich.reimer@uni-jena.de)
- Sean MacAvaney
- Benno Stein
- Matthias Hagen
- Martin Potthast

We're happy to help!

<!--## Citation

If you use our resources or its tutorials in your research, please cite the following paper:

> TODO

You can use the following BibTeX entry for citation:

```bibtex
% TODO
```-->

## License

This repository and its tutorials are released under the [MIT license](LICENSE).
<!-- If you use the resources in your research, we'd be glad if you'd [cite us](#citation). -->

<!-- ## Abstract

> TODO -->
