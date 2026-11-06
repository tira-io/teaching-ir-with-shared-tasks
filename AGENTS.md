# AGENTS.md

Instructions for coding agents working in this repository.

Docs: [README.md](README.md) (overview, course list), [teaching.md](teaching.md) (CLI workflow for teachers), [tutorials/README.md](tutorials/README.md) (tutorial index and how to run them), [dashboard/README.md](dashboard/README.md). Keep these in sync when changing CLI commands or adding tutorials.

## Commands

```shell
pip install -e '.[tests]'   # in a venv, Python >=3.10
ruff check cli
mypy cli
pytest --cov=cli cli
```

```shell
cd dashboard
python3 process_data.py     # pre-processes links.yml (needs pyyaml); run before building
yarn && yarn lint && yarn build   # also: yarn dev
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs all of these, with mypy and pytest on Python 3.10–3.13. It also builds the dev container image from [.devcontainer/Dockerfile](.devcontainer/Dockerfile) on every push. Deployment only runs on version tags (e.g., `0.0.3`) on `main`: it publishes the image to `ghcr.io/tira-io/teaching-ir-with-shared-tasks` (`:<version>` and `:latest`) and deploys `dashboard/dist/` to GitHub Pages.

## CLI architecture

[cli/\_\_main\_\_.py](cli/__main__.py) defines all click commands. Commands are thin: they parse arguments and lazily import (inside the function body) the module that does the work, so heavy dependencies (PyTerrier/Java, doccano-client, TIRA) only load when needed. Follow this pattern for new commands.

| Module | Responsibility |
|---|---|
| [cli/topics.py](cli/topics.py) | Google Forms topics CSV → TREC-style `topics.xml`; resolves ChatNoir cache URLs to docnos (HTTP cached in `.web_cache/`) |
| [cli/documents.py](cli/documents.py) | Google Forms document-collection CSV → `documents/<id>/{documents.jsonl,metadata.yml}` plus merged collection; downloads Google Drive files (cached in `.drive_cache/`) |
| [cli/chatnoir_docker.py](cli/chatnoir_docker.py) | `build-chatnoir`: drives Docker via `subprocess` to start an all-in-one ChatNoir container, index corpora, commit it to an image, and emit a Kubernetes manifest |
| [cli/docker_assets/index_local_corpus.py](cli/docker_assets/index_local_corpus.py) | Mounted into the *unmodified* `chatnoir-ir-datasets-indexer` image; monkey-patches it to index a local `documents.jsonl` and upload it to MinIO. Runs inside that image, not in this venv (imports `boto3`, `chatnoir_ir_datasets_indexer`) |
| [cli/tirex.py](cli/tirex.py) | Pooling: ChatNoir + PyTerrier baseline runs → trectools pool → `doccano-judgment-pool.jsonl`; also corpus subsampling and TIRA group creation |
| [cli/judgments.py](cli/judgments.py) | Doccano: create per-group users/projects and upload pools; export qrels; clean up. Default annotation guidelines in [cli/guidelines.md](cli/guidelines.md) (shipped as package data) |
| [cli/utils.py](cli/utils.py) | Shared helpers (e.g. `group_user_name`) |

`create-tira-groups` and `subsample-corpus` are not in [teaching.md](teaching.md); see their `--help`.

Most commands operate on a **course directory** whose `config.json` is written by `init-directory` with keys `course-name`, `chatnoir-image-repository`, `corpora-base`, `topics`, `runs`, `team-mapping`. Other files in it by convention: `topic-mapping.jsonl`, `doccano-label-configs.json`, `documents.jsonl.gz`, `pyterrier-index/`, `doccano-judgment-pool.jsonl`, `kubernetes.yaml`, `tira-invites.json`.

## Gotchas

- `pool-documents` additionally needs `chatnoir-index` (and optionally `irds-id`) in `config.json`, which `init-directory` does not write; it also hard-codes `topic-mapping.jsonl` instead of reading `team-mapping`. It never overwrites an existing `doccano-judgment-pool.jsonl`.
- `build-chatnoir` expects the Docker images `chatnoir-complete:local` and `chatnoir-ir-datasets-indexer:local` to already exist locally, and discovers corpora as subdirectories of `corpora-base` that contain a `documents.jsonl` (`docno`/`url`/`title`/`text` per line).
- Doccano credentials can come from `DOCCANO_URL`, `DOCCANO_USERNAME`, `DOCCANO_PASSWORD` env vars (otherwise prompted).
- Topic/document CSV column names are tied to the Google Forms (some German, e.g. `Zeitstempel`).
- `doccano-client` is pinned to a git fork (see comment in [pyproject.toml](pyproject.toml)); don't swap it for the PyPI release.
- Working data in the repo root (`documents/`, `topics*.xml`, `*-submission.csv`, `.drive_cache/`, `.web_cache/`, `.pooling-cache/`) is local course data; don't commit or delete it unprompted.
- The `# noqa` suppressions in `chatnoir_docker.py` are intended: `S603`/`S607` for the `docker` CLI calls (argument lists, no shell) and `S105` for the image's local default credentials.

## Tests

Tests live next to the code as `cli/test_<module>.py` and must not need Docker, a Doccano instance, or network access (fake lookups with `monkeypatch`). Existing tests cover topics conversion and docno resolution, corpus discovery and the Kubernetes manifest, Doccano naming helpers, and `group_user_name`. Not yet covered: [cli/documents.py](cli/documents.py) (document-collection CSV → metadata, Google Drive URL parsing).
