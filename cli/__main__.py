from pathlib import Path
from secrets import choice
from string import digits
from typing import Any, Mapping, Sequence

import json
from click import Context, Parameter
from click import Path as PathType
from click import argument, echo, group, option
from pandas import DataFrame, concat, read_json, read_xml
from tqdm import tqdm

from cli import __version__ as app_version
from cli import chatnoir_docker


def print_version(
    context: Context,
    _parameter: Parameter,
    value: Any,
) -> None:
    if not value or context.resilient_parsing:
        return
    echo(app_version)
    context.exit()


def read_pooled_for_topics(pool_path: Sequence[Path], topics: DataFrame) -> DataFrame:
    # Explicitly select only the columns we need.
    columns = ["query_id", "query", "description", "narrative", "doc_id", "text"]
    ret = concat(
        read_json(
            path,
            lines=True,
            dtype={column: str for column in columns},
        )[columns]
        for path in tqdm(
            pool_path,
            desc="Read pooled documents",
            unit="path",
        )
    )
    echo(f"Found {len(ret)} pooled documents.")

    return ret.merge(topics, how="inner", on="query_id")


def group_names(pool: DataFrame, project_prefix: str) -> Mapping[str, str]:
    from cli.utils import group_user_name

    groups: set[str] = set((i for i in pool["group"].to_list() if i))
    echo(f"Found {len(groups)} groups: {', '.join(sorted(groups))}")

    # Create mapping of groups to usernames and project names.
    return {group: group_user_name(project_prefix, group) for group in groups}


@group()
@option(
    "-V",
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
def cli() -> None:
    pass


_DEFAULT_TOPICS_FILENAME = "topics.xml"
_DEFAULT_RUNS_DIRNAME = "runs"
_DEFAULT_CORPORA_BASE_DIRNAME = "corpora"
_DEFAULT_TEAM_MAPPING_FILENAME = "topic-mapping.jsonl"
_DOCCANO_LABEL_CONFIGS_FILENAME = "doccano-label-configs.json"
# Matches the "relevant"/"not relevant" label scheme already assumed by
# `export_relevance_judgments` (which parses the judgment value out of the
# trailing "(N)" in the label text).
_DEFAULT_DOCCANO_LABEL_CONFIGS = [
    {
        "id": None,
        "text": "Not Relevant (0)",
        "prefixKey": None,
        "suffixKey": "0",
        "backgroundColor": "#D33115",
        "textColor": "#ffffff",
    },
    {
        "id": None,
        "text": "Relevant (1)",
        "prefixKey": None,
        "suffixKey": "1",
        "backgroundColor": "#194D33",
        "textColor": "#ffffff",
    },
]


@cli.command()
@argument(
    "directory",
    type=PathType(
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@argument("course_name", type=str)
@option(
    "--chatnoir-image-repository",
    "chatnoir_image_repository",
    type=str,
    default=chatnoir_docker._DEFAULT_RESULT_IMAGE_REPOSITORY,
    show_default=True,
    help="Image repository that 'build-chatnoir' commits/tags the course's finished ChatNoir image to (tagged with COURSE_NAME).",
)
@option(
    "--corpora-base",
    "corpora_base_dirname",
    type=str,
    default=_DEFAULT_CORPORA_BASE_DIRNAME,
    show_default=True,
    help="Name (relative to DIRECTORY, usually on Ceph) of the directory where this course's submitted corpora/data files are stored.",
)
@option(
    "--topics",
    "topics_filename",
    type=str,
    default=_DEFAULT_TOPICS_FILENAME,
    show_default=True,
    help="Filename (relative to DIRECTORY) of the topics XML file created later by convert-topics-csv-to-xml.",
)
@option(
    "--runs",
    "runs_dirname",
    type=str,
    default=_DEFAULT_RUNS_DIRNAME,
    show_default=True,
    help="Name (relative to DIRECTORY) of the directory that will hold retrieval runs.",
)
@option(
    "--team-mapping",
    "team_mapping_filename",
    type=str,
    default=_DEFAULT_TEAM_MAPPING_FILENAME,
    show_default=True,
    help="Filename (relative to DIRECTORY) of the account-to-topics mapping file.",
)
@option(
    "--force/--no-force",
    default=False,
    help="Overwrite configuration files that already exist in DIRECTORY.",
)
def init_directory(
    directory: Path,
    course_name: str,
    chatnoir_image_repository: str,
    corpora_base_dirname: str,
    topics_filename: str,
    runs_dirname: str,
    team_mapping_filename: str,
    force: bool,
) -> None:
    """
    Set up a new DIRECTORY with the basic configuration needed by the later
    steps of the shared task (pooling, relevance judgment preparation and
    export, etc.), so that it does not need to be assembled by hand.

    COURSE_NAME identifies this course's run (e.g., "wise-2026"); it is used
    as the Docker image tag for the ChatNoir image built by build-chatnoir.

    This creates, inside DIRECTORY:

    \b
    - config.json, pointing to the corpora base directory, topics file,
      runs directory, and team mapping file, and storing the course name
      and ChatNoir image repository
    - (initially empty) corpora/ and runs/ directories
    - an (initially empty) team-mapping file to fill in once
      topics have been submitted and accounts assigned
    - doccano-label-configs.json with the default relevant/not-relevant
      label scheme used when preparing and exporting relevance judgments
    """
    config_path = directory / "config.json"
    team_mapping_path = directory / team_mapping_filename
    label_configs_path = directory / _DOCCANO_LABEL_CONFIGS_FILENAME
    runs_path = directory / runs_dirname
    corpora_base_path = directory / corpora_base_dirname

    if not force:
        existing = [path for path in (config_path, team_mapping_path, label_configs_path) if path.exists()]
        if len(existing) > 0:
            raise FileExistsError(
                f"Refusing to overwrite existing file(s): {', '.join(str(path) for path in existing)}. "
                "Use --force to overwrite."
            )

    directory.mkdir(parents=True, exist_ok=True)
    runs_path.mkdir(parents=True, exist_ok=True)
    echo(f"Created directory '{runs_path}'.")
    corpora_base_path.mkdir(parents=True, exist_ok=True)
    echo(f"Created directory '{corpora_base_path}'.")

    config = {
        "course-name": course_name,
        "chatnoir-image-repository": chatnoir_image_repository,
        "corpora-base": corpora_base_dirname,
        "topics": topics_filename,
        "runs": runs_dirname,
        "team-mapping": team_mapping_filename,
    }
    with config_path.open("wt") as file:
        json.dump(config, file, indent=4)
        file.write("\n")
    echo(f"Wrote '{config_path}'.")

    if not team_mapping_path.exists():
        team_mapping_path.touch()
    echo(
        f"Created empty '{team_mapping_path}'. "
        'Fill in once topics have been submitted, with one JSON object per line, e.g.: '
        '{"account": "ir-25-fsu-51", "topics": ["51"]}'
    )

    with label_configs_path.open("wt") as file:
        json.dump(_DEFAULT_DOCCANO_LABEL_CONFIGS, file, indent=4)
        file.write("\n")
    echo(f"Wrote '{label_configs_path}'.")

    echo(f"Initialized directory '{directory}'.")


@cli.command()
@argument(
    "directory",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@option(
    "--chatnoir-image",
    default=chatnoir_docker._DEFAULT_CHATNOIR_IMAGE,
    show_default=True,
    help="Docker image bundling Elasticsearch, MinIO, and ChatNoir (see docker/all-in-one in the chatnoir-web repo).",
)
@option(
    "--indexer-image",
    default=chatnoir_docker._DEFAULT_INDEXER_IMAGE,
    show_default=True,
    help="Docker image of the chatnoir-ir-datasets-indexer.",
)
def build_chatnoir(
    directory: Path,
    chatnoir_image: str,
    indexer_image: str,
) -> None:
    """
    Start ChatNoir (bundled with Elasticsearch and MinIO in a single Docker
    container) and index all corpora found in DIRECTORY (as set up by
    init-directory) into it with the chatnoir-ir-datasets-indexer Docker
    image, so that they can be searched through the ChatNoir UI.

    DIRECTORY must already contain a config.json (see init-directory), with
    corpora placed under its corpora-base directory, each in its own
    subdirectory with a documents.jsonl file (one JSON object per line, with
    docno/url/title/text fields).

    Both Docker images must already be built locally (or otherwise available
    to the local Docker daemon) before running this command.

    Once indexing is done, the resulting container is committed to a Docker
    image (tagged with this course's course-name, see init-directory) and
    then stopped and removed, so that the course's ChatNoir deployment is
    fully captured in that image. Two tags are created, a versioned one
    (<course-name>-<5 random digits>) and a '-latest' alias; both still need
    to be pushed manually (instructions are printed at the end).

    A Kubernetes manifest (Deployment, Service, Ingress exposing search and
    the cache/document view on two public hostnames) is also written to
    kubernetes.yaml in the course directory, along with a 'kubectl apply'
    instruction to deploy it once the '-latest' image has been pushed.
    """
    with (directory / "config.json").open("rt") as file:
        config = json.load(file)
    corpora_base_path = directory / config["corpora-base"]

    if "course-name" not in config:
        raise ValueError(
            "config.json has no 'course-name'. Re-run 'teaching-ir init-directory "
            f"{directory} <COURSE_NAME>' or add a \"course-name\" entry to "
            f"'{directory / 'config.json'}' by hand."
        )
    course_name = config["course-name"]
    image_repository = config.get(
        "chatnoir-image-repository", chatnoir_docker._DEFAULT_RESULT_IMAGE_REPOSITORY
    )
    version_suffix = "".join(choice(digits) for _ in range(5))
    image_tag_versioned = f"{image_repository}:{course_name}-{version_suffix}"
    image_tag_latest = f"{image_repository}:{course_name}-latest"

    corpora = chatnoir_docker.discover_corpora(corpora_base_path)
    if not corpora:
        raise FileNotFoundError(
            f"No corpora with a documents.jsonl file found in '{corpora_base_path}'."
        )
    echo(f"Found {len(corpora)} corpora: {', '.join(c.directory.name for c in corpora)}")

    container_name = chatnoir_docker.container_name_for(directory)
    network_name = chatnoir_docker.network_name_for(container_name)
    ports = {port: None for port in chatnoir_docker._CONTAINER_PORTS}

    chatnoir_docker.ensure_chatnoir_container(container_name, network_name, chatnoir_image, ports)
    chatnoir_docker.wait_for_elasticsearch(container_name)

    es_host = f"http://{container_name}:9200"
    s3_endpoint = f"http://{container_name}:9000"
    for corpus in corpora:
        chatnoir_docker.index_corpus(network_name, es_host, s3_endpoint, indexer_image, corpus)
    chatnoir_docker.refresh_indices(container_name, corpora)

    needs_restart = chatnoir_docker.update_search_indices(container_name, corpora)
    if needs_restart:
        chatnoir_docker.restart_container(container_name)
        chatnoir_docker.wait_for_elasticsearch(container_name)

    chatnoir_docker.commit_and_remove_container(
        container_name, network_name, [image_tag_versioned, image_tag_latest]
    )

    echo("")
    echo(
        f"Built ChatNoir image for course '{course_name}': "
        f"{image_tag_versioned} (also tagged as {image_tag_latest})"
    )
    echo("")
    echo("To start it locally, run:")
    echo(f"  docker run --rm --net host --name {container_name} {image_tag_latest}")
    echo(
        "  (then open http://127.0.0.1:8000/ for search, "
        "http://127.0.0.1:8001/ for the cache/view; get a demo API key with "
        f"'docker exec {container_name} cat /opt/chatnoir-web/demo-apikey.txt')"
    )
    echo("")
    echo("To push both tags (requires 'docker login ghcr.io' with access to the repository), run:")
    echo(f"  docker push {image_tag_versioned}")
    echo(f"  docker push {image_tag_latest}")

    manifest = chatnoir_docker.kubernetes_manifest(course_name, image_tag_latest)
    manifest_path = directory / "kubernetes.yaml"
    manifest_path.write_text(manifest)
    echo("")
    echo(f"Wrote a Kubernetes manifest (Deployment, Service, Ingress) to '{manifest_path}'.")
    echo("To deploy it (requires the image to already be pushed and public), run:")
    echo(f"  kubectl apply -f {manifest_path}")


@cli.command()
@argument(
    "csv_path",
    type=PathType(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@argument(
    "topics_path",
    type=PathType(
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=False,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@option(
    "--release/--no-release",
    type=bool,
    default=False,
)
@option(
    "--coauthors-path",
    type=PathType(
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=False,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@option(
    "--from-date",
    type=str,
    default=None,
)
@option(
    "--filter-university",
    type=str,
    default=None,
)
def convert_topics_csv_to_xml(
    csv_path: Path,
    topics_path: Path,
    release: bool,
    coauthors_path: Path | None,
    from_date: str | None,
    filter_university: str | None,
) -> None:
    """
    Convert a topics spread sheet exported from Google Forms as CSV to a topics XML file.
    """
    from cli.topics import convert_topics_csv_to_xml
    
    convert_topics_csv_to_xml(
        csv_path=csv_path,
        topics_path=topics_path,
        release=release,
        coauthors_path=coauthors_path,
        from_date=from_date,
        filter_university=filter_university,
    )


@cli.command()
@argument(
    "course_path",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@option(
    "--pooling-depth",
    type=int,
    default=1000,
    help="Pooling depth.",
)
def subsample_corpus(
    course_path: Path,
    pooling_depth: int,
) -> None:
    """
    Create a subsample of a potentially huge corpus for experiments against a fixed set of corpora.
    """
    from cli.tirex import subsample_corpus
    subsample_corpus(course_path / 'qrels.txt', course_path, pooling_depth)


@cli.command()
@argument(
    "directory",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@option(
    "--pooling-depth",
    type=int,
    default=10,
    help="Pooling depth.",
)
def pool_documents(
    directory: Path,
    pooling_depth: int,
) -> None:
    """
    Create top-k pools of documents retrieved by TIREx baselines using ChatNoir.
    """
    from cli.tirex import pool_documents

    pool_documents(
        path=directory,
        pooling_depth=pooling_depth,
    )


def read_topics(topics_path: Path):
    ret = read_xml(
        topics_path,
        dtype=str,
    )[
        [
            # Explicitly select only the columns we need.
            "number",
            "group",
        ]
    ].rename(columns={"number": "query_id"})

    echo(f"Found {len(ret)} topics.")
    return ret


@cli.command()
@option(
    "-d",
    "--doccano-url",
    type=str,
    required=True,
    prompt="Doccano URL",
    envvar="DOCCANO_URL",
    help="Base URL of the Doccano instance to use.",
    metavar="URL",
)
@option(
    "-u",
    "--doccano-username",
    type=str,
    required=True,
    prompt="Doccano username",
    envvar="DOCCANO_USERNAME",
    help="Username to authenticate with Doccano.",
)
@option(
    "-p",
    "--doccano-password",
    type=str,
    required=True,
    prompt="Doccano password",
    hide_input=True,
    envvar="DOCCANO_PASSWORD",
    help="Password to authenticate with Doccano.",
)
@option(
    "-g",
    "--guidelines-path",
    type=PathType(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
    help="Path to a markdown (.md) file containing annotation guidelines.",
)
@option(
    "-m",
    "--supervisor-member",
    "extra_supervisors",
    type=str,
    multiple=True,
    help="Doccano usernames of additional supervisors to add to each project (besides the authenticated user).",
)
@option(
    "--skip-existing/--no-skip-existing",
    type=bool,
    default=False,
    help="Skip projects that already contain documents (e.g., to resume an interrupted run).",
)
@argument(
    "prefix",
    type=str,
)
@argument(
    "path",
    type=PathType(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
def prepare_relevance_judgments(
    doccano_url: str,
    doccano_username: str,
    doccano_password: str,
    guidelines_path: Path | None,
    extra_supervisors: Sequence[str],
    skip_existing: bool,
    prefix: str,
    path: Path,
) -> None:
    """
    Prepare the relevance judgments on Doccano for pooled documents stored in JSON Lines files.
    This script will automatically create users and projects, and upload the pooled documents for each group.
    PREFIX is the common prefix of the generated project and user names.
    """
    from cli.judgments import prepare_relevance_judgments

    prepare_relevance_judgments(
        doccano_url=doccano_url,
        doccano_username=doccano_username,
        doccano_password=doccano_password,
        guidelines_path=guidelines_path,
        extra_supervisors=extra_supervisors,
        prefix=prefix,
        path=path,
        skip_existing=skip_existing,
    )



@cli.command()
@option(
    "-d",
    "--doccano-url",
    type=str,
    required=True,
    prompt="Doccano URL",
    envvar="DOCCANO_URL",
    help="Base URL of the Doccano instance to use.",
    metavar="URL",
)
@option(
    "-u",
    "--doccano-username",
    type=str,
    required=True,
    prompt="Doccano username",
    envvar="DOCCANO_USERNAME",
    help="Username to authenticate with Doccano.",
)
@option(
    "-p",
    "--doccano-password",
    type=str,
    required=True,
    prompt="Doccano password",
    hide_input=True,
    envvar="DOCCANO_PASSWORD",
    help="Password to authenticate with Doccano.",
)
@argument(
    "prefix",
    type=str,
)
@argument(
    "directory",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    )
)
def export_relevance_judgments(
    doccano_url: str,
    doccano_username: str,
    doccano_password: str,
    prefix: str,
    directory: Path,
) -> None:
    """
    Export the relevance judgments from Doccano for pooled documents from JSON Lines files specified in POOLED_DOCUMENTS_PATHS.
    The relevance judgments will be saved in the TREC qrels format to QRELS_PATH.
    PREFIX is the common prefix of the generated project and user names.
    """
    from cli.judgments import export_relevance_judgments

    export_relevance_judgments(
        doccano_url=doccano_url,
        doccano_username=doccano_username,
        doccano_password=doccano_password,
        prefix=prefix,
        directory=directory,
    )


@cli.command()
@option(
    "-d",
    "--doccano-url",
    type=str,
    required=True,
    prompt="Doccano URL",
    envvar="DOCCANO_URL",
    help="Base URL of the Doccano instance to use.",
    metavar="URL",
)
@option(
    "-u",
    "--doccano-username",
    type=str,
    required=True,
    prompt="Doccano username",
    envvar="DOCCANO_USERNAME",
    help="Username to authenticate with Doccano.",
)
@option(
    "-p",
    "--doccano-password",
    type=str,
    required=True,
    prompt="Doccano password",
    hide_input=True,
    envvar="DOCCANO_PASSWORD",
    help="Password to authenticate with Doccano.",
)
@argument(
    "prefix",
    type=str,
)
def clean_up(
    doccano_url: str,
    doccano_username: str,
    doccano_password: str,
    prefix: str,
) -> None:
    """
    Clean up automatically created projects and users.
    PREFIX is the common prefix of the generated project and user names.
    """
    from cli.judgments import clean_up

    clean_up(
        doccano_url=doccano_url,
        doccano_username=doccano_username,
        doccano_password=doccano_password,
        prefix=prefix,
    )

@cli.command()
@argument(
    "prefix",
    type=str,
)
@argument(
    "path",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@argument(
    "tira_task_id",
    type=str,
)
@argument(
    "affiliation_of_teams",
    type=str,
)
@argument(
    "country_of_teams",
    type=str,
)
def create_tira_groups(
    prefix: str,
    path: Path,
    tira_task_id: str,
    affiliation_of_teams: str,
    country_of_teams: str,
) -> None:
    """
    Create the groups in tira.
    """

    from cli.tirex import create_group

    topics = read_topics(path / "topics.xml")
    pool = read_pooled_for_topics([path / "doccano-judgment-pool.jsonl"], topics)
    groups = group_names(pool, prefix).values()

    for group_name in [i for i in groups if 'tutors' not in i.lower()]:
        create_group(
            path / "tira-invites.json",
            tira_task_id,
            group_name,
            affiliation_of_teams,
            country_of_teams,
        )


if __name__ == "__main__":
    # pylint: disable=E1120
    cli()
