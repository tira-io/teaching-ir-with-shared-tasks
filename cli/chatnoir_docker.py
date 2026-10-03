"""
Docker-based orchestration for `teaching-ir build-chatnoir`.

Starts the all-in-one ChatNoir Docker image (Elasticsearch, MinIO, and
ChatNoir itself) and uses the `chatnoir-ir-datasets-indexer` Docker image
to index all corpora found in a course directory (as set up by
`teaching-ir init-directory`) into it, so that they become searchable
through the ChatNoir UI.
"""
import json
import subprocess
from importlib.resources import as_file, files
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Mapping, MutableMapping, NamedTuple, Optional, Sequence

from click import echo
from slugify import slugify

try:
    from yaml import safe_load as _yaml_safe_load  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - PyYAML is pulled in transitively.
    _yaml_safe_load = None

_DEFAULT_CHATNOIR_IMAGE = "chatnoir-complete:local"
_DEFAULT_INDEXER_IMAGE = "chatnoir-ir-datasets-indexer:local"
_DEFAULT_RESULT_IMAGE_REPOSITORY = "ghcr.io/tira-io/teaching-ir-with-shared-tasks/chatnoir"
_DEFAULT_ES_USERNAME = "chatnoir"
_DEFAULT_ES_PASSWORD = "chatnoir"
# MinIO root credentials baked into the chatnoir-complete image by default
# (see docker/all-in-one/local_settings.template.py in chatnoir-web).
_DEFAULT_S3_ACCESS_KEY = "chatnoir"
_DEFAULT_S3_SECRET_KEY = "chatnoirchatnoir"
# Shared bucket all course corpora are uploaded to (one object per corpus),
# analogous to multi-corpus buckets like 'corpora-tirex-small'.
_S3_BUCKET = "course-corpora"
_CONTAINER_PORTS = (8000, 8001, 9200, 9000, 9001)
_HEALTH_CHECK_TIMEOUT_SECONDS = 180
_HEALTH_CHECK_INTERVAL_SECONDS = 2


class Corpus(NamedTuple):
    directory: Path
    corpus_id: str
    meta_index: str
    data_index: str
    display_name: str


def _run(command: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, **kwargs)


def container_name_for(directory: Path) -> str:
    return f"chatnoir-{slugify(directory.name)}"


def network_name_for(container_name: str) -> str:
    return f"{container_name}-net"


def _ensure_network(network_name: str) -> None:
    exists = subprocess.run(
        ["docker", "network", "inspect", network_name],
        capture_output=True,
        text=True,
    ).returncode == 0
    if not exists:
        _run(["docker", "network", "create", network_name])
        echo(f"Created Docker network '{network_name}'.")


def _container_status(container_name: str) -> Optional[str]:
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", container_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def ensure_chatnoir_container(
    container_name: str,
    network_name: str,
    image: str,
    ports: Mapping[int, Optional[int]],
) -> None:
    """
    Ensures a `chatnoir-complete` container with the given name is running,
    starting a new one (or restarting an existing, stopped one) if needed.
    """
    status = _container_status(container_name)
    if status == "running":
        echo(f"Reusing already-running container '{container_name}'.")
        return
    if status is not None:
        _run(["docker", "start", container_name])
        echo(f"Restarted existing container '{container_name}'.")
        return

    _ensure_network(network_name)

    command = [
        "docker", "run", "-d",
        "--name", container_name,
        "--network", network_name,
    ]
    for container_port, host_port in ports.items():
        if host_port is not None:
            command += ["-p", f"{host_port}:{container_port}"]
        else:
            command += ["-p", str(container_port)]
    command.append(image)
    _run(command)
    echo(f"Started container '{container_name}' from image '{image}'.")


def published_ports(container_name: str) -> Mapping[int, int]:
    result = _run(
        ["docker", "inspect", "-f", "{{json .NetworkSettings.Ports}}", container_name],
        capture_output=True,
    )
    raw = json.loads(result.stdout)
    ports = {}
    for container_port, bindings in raw.items():
        if not bindings:
            continue
        port_number = int(container_port.split("/")[0])
        ports[port_number] = int(bindings[0]["HostPort"])
    return ports


def wait_for_elasticsearch(container_name: str) -> None:
    echo("Waiting for Elasticsearch to become available...")
    deadline = monotonic() + _HEALTH_CHECK_TIMEOUT_SECONDS
    while monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", container_name, "curl", "-sf", "http://127.0.0.1:9200"],
            capture_output=True,
        )
        if result.returncode == 0:
            echo("Elasticsearch is up.")
            return
        sleep(_HEALTH_CHECK_INTERVAL_SECONDS)
    raise TimeoutError(
        f"Elasticsearch in container '{container_name}' did not become "
        f"available within {_HEALTH_CHECK_TIMEOUT_SECONDS} seconds."
    )


def _corpus_display_name(directory: Path, corpus_id: str) -> str:
    metadata_path = directory / "metadata.yml"
    if metadata_path.is_file() and _yaml_safe_load is not None:
        try:
            metadata = _yaml_safe_load(metadata_path.read_text()) or {}
            name = metadata.get("dataset", {}).get("name")
            if name:
                return str(name)
        except Exception:  # noqa: BLE001 - metadata is best-effort only.
            pass
    return corpus_id


def discover_corpora(corpora_base_path: Path) -> Sequence[Corpus]:
    corpora = []
    for directory in sorted(corpora_base_path.iterdir()):
        if not directory.is_dir():
            continue
        if not (directory / "documents.jsonl").is_file():
            continue
        corpus_id = slugify(directory.name, separator="_")
        corpora.append(Corpus(
            directory=directory,
            corpus_id=corpus_id,
            meta_index=f"chatnoir_meta_{corpus_id}",
            data_index=f"chatnoir_data_{corpus_id}",
            display_name=_corpus_display_name(directory, corpus_id),
        ))
    return corpora


def index_corpus(
    network_name: str,
    es_host: str,
    s3_endpoint: str,
    indexer_image: str,
    corpus: Corpus,
) -> None:
    echo(f"Indexing corpus '{corpus.directory.name}' into "
         f"'{corpus.meta_index}'/'{corpus.data_index}'...")
    script_resource = files("cli.docker_assets").joinpath("index_local_corpus.py")
    with as_file(script_resource) as script_path:
        _run([
            "docker", "run", "--rm",
            "--network", network_name,
            "--entrypoint", "python3",
            "-v", f"{script_path}:/scripts/index_local_corpus.py:ro",
            "-v", f"{corpus.directory.resolve()}:/corpus/{corpus.corpus_id}:ro",
            indexer_image,
            "/scripts/index_local_corpus.py",
            es_host,
            _DEFAULT_ES_USERNAME,
            _DEFAULT_ES_PASSWORD,
            corpus.meta_index,
            corpus.data_index,
            f"/corpus/{corpus.corpus_id}",
            s3_endpoint,
            _DEFAULT_S3_ACCESS_KEY,
            _DEFAULT_S3_SECRET_KEY,
            _S3_BUCKET,
        ])
    echo(f"Indexed corpus '{corpus.directory.name}'.")


def refresh_indices(container_name: str, corpora: Sequence[Corpus]) -> None:
    for corpus in corpora:
        for index in (corpus.meta_index, corpus.data_index):
            subprocess.run(
                ["docker", "exec", container_name, "curl", "-sf", "-X", "POST",
                 f"http://127.0.0.1:9200/{index}/_refresh"],
                capture_output=True,
            )


_LOCAL_SETTINGS_PATH = "/opt/chatnoir-web/chatnoir/chatnoir/local_settings.py"


# The all-in-one image's baked-in local_settings.py ships a demo 'cranfield'
# entry (pointing at indices that don't exist in freshly started containers)
# purely for its own standalone demo purposes. It is irrelevant for an actual
# course deployment, so it is dropped the first time we touch SEARCH_INDICES.
_DEMO_SEARCH_INDEX_ID = "cranfield"


def update_search_indices(container_name: str, corpora: Sequence[Corpus]) -> bool:
    """
    Registers any not-yet-registered corpora in the container's
    `local_settings.py` `SEARCH_INDICES` (dropping the image's baked-in demo
    'cranfield' entry, which does not correspond to any data in this
    container), so they show up in the ChatNoir UI. Returns whether the
    container needs to be restarted to pick this up.
    """
    current = _run(
        ["docker", "exec", container_name, "cat", _LOCAL_SETTINGS_PATH],
        capture_output=True,
    ).stdout

    drop_demo_entry = (
        f"'{_DEMO_SEARCH_INDEX_ID}'" in current
        or f'"{_DEMO_SEARCH_INDEX_ID}"' in current
    )

    new_entries: MutableMapping[str, Mapping[str, Any]] = {}
    for corpus in corpora:
        if f"'{corpus.corpus_id}'" in current or f'"{corpus.corpus_id}"' in current:
            continue
        new_entries[corpus.corpus_id] = {
            "index": corpus.data_index,
            "warc_index": corpus.meta_index,
            "warc_bucket": _S3_BUCKET,
            "warc_uuid_prefix": corpus.corpus_id,
            "display_name": corpus.display_name,
            "compat_search_versions": [1],
            # ChatNoir combines all indices with 'default': True when no
            # explicit `index` is given, so marking every course corpus as
            # default makes a plain search cover all of them combined.
            "default": True,
        }

    if not new_entries and not drop_demo_entry:
        return False

    snippet_lines = ["", "# Added by `teaching-ir build-chatnoir`."]
    if drop_demo_entry:
        snippet_lines.append(
            f"SEARCH_INDICES.pop({_DEMO_SEARCH_INDEX_ID!r}, None)  # unrelated demo entry"
        )
    if new_entries:
        snippet_lines.append("SEARCH_INDICES.update({")
        for corpus_id, entry in new_entries.items():
            snippet_lines.append(f"    {corpus_id!r}: {entry!r},")
        snippet_lines.append("})")
    # Corpora registered by a previous, older run of this command may not
    # have been marked as default yet; make sure every course corpus is,
    # so a plain search (no explicit `index`) covers all of them combined.
    already_registered_ids = [
        corpus.corpus_id for corpus in corpora if corpus.corpus_id not in new_entries
    ]
    for corpus_id in already_registered_ids:
        snippet_lines.append(
            f"SEARCH_INDICES[{corpus_id!r}]['default'] = True"
        )
    snippet = "\n".join(snippet_lines) + "\n"

    subprocess.run(
        ["docker", "exec", "-i", container_name, "sh", "-c",
         f"cat >> {_LOCAL_SETTINGS_PATH}"],
        input=snippet,
        text=True,
        check=True,
    )
    echo(f"Registered {len(new_entries)} new search index(es) in '{container_name}'.")
    return True


def restart_container(container_name: str) -> None:
    echo(f"Restarting container '{container_name}' to apply configuration changes...")
    _run(["docker", "restart", container_name])


def commit_and_remove_container(
    container_name: str, network_name: str, image_tags: Sequence[str]
) -> None:
    """
    Commits the (already fully set up and indexed) container to the first of
    `image_tags`, tags the result with any remaining `image_tags` as well,
    then stops and removes the container and its network so that the only
    way to use this course's ChatNoir deployment going forward is through
    the committed image(s).
    """
    primary_tag, *alias_tags = image_tags
    echo(f"Committing container '{container_name}' to image '{primary_tag}'...")
    _run(["docker", "commit", container_name, primary_tag])
    for alias_tag in alias_tags:
        _run(["docker", "tag", primary_tag, alias_tag])
    _run(["docker", "stop", container_name])
    _run(["docker", "rm", container_name])
    subprocess.run(["docker", "network", "rm", network_name], capture_output=True)
    echo(f"Stopped and removed container '{container_name}'.")
