from importlib.resources import files
from json import JSONDecodeError
from pathlib import Path
from secrets import choice
from string import ascii_letters, digits
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Annotated, Any, Mapping, Sequence, TypeAlias
from urllib.parse import urljoin
from warnings import warn
from webbrowser import open as open_webbrowser
from zipfile import ZipFile

from annotated_types import Len
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from click import (
    argument,
    confirm,
    group,
    Context,
    Parameter,
    echo,
    option,
    Path as PathType,
)
from doccano_client import DoccanoClient
from doccano_client.exceptions import DoccanoAPIError
from doccano_client.models.user import User
from doccano_client.models.project import Project
from doccano_client.models.label_type import LabelType
from doccano_client.models.member import Member
from doccano_client.models.data_upload import Task as DataUploadTask
from pandas import DataFrame, concat, read_json, read_csv, isna, read_xml, to_datetime
from requests import RequestException, session
from slugify import slugify
from tqdm import tqdm

from cli import __version__ as app_version


def print_version(
    context: Context,
    _parameter: Parameter,
    value: Any,
) -> None:
    if not value or context.resilient_parsing:
        return
    echo(app_version)
    context.exit()


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


_session = session()
_cache = FileCache(".web_cache", forever=True)
_session = CacheControl(_session, _cache)


def _chatnoir_cache_url_to_docno(url: str) -> str | None:
    try:
        response = _session.get(f"{url}&raw", timeout=60)
        response.raise_for_status()
    except RequestException:
        return None
    try:
        json = response.json()
    except JSONDecodeError:
        return None
    for key in ("doc_id", "docid", "docno"):
        if key in json:
            return json[key]
    return None


def _chatnoir_cache_urls_to_docnos(*url: str) -> str:
    res = (_chatnoir_cache_url_to_docno(x) for x in url if not isna(x))
    return ",".join(x for x in res if x is not None)


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
def convert_topics_csv_to_xml(
    csv_path: Path,
    topics_path: Path,
    release: bool,
    coauthors_path: Path | None,
) -> None:
    """
    Convert a topics spread sheet exported from Google Forms as CSV to a topics XML file.
    """
    df = read_csv(csv_path)
    df.rename(
        columns={
            "Zeitstempel": "timestamp",
            "Title": "title",
            "Description": "description",
            "Narrative": "narrative",
            "Relevant document #1": "relevant_chatnoir_url_1",
            "Relevant document #2": "relevant_chatnoir_url_2",
            "Relevant document #3": "relevant_chatnoir_url_3",
            "Irrelevant document #1": "irrelevant_chatnoir_url_1",
            "Irrelevant document #2": "irrelevant_chatnoir_url_2",
            "Irrelevant document #3": "irrelevant_chatnoir_url_3",
            "Full name": "author",
            "Group name": "group",
            "University": "university",
            "Do you consent to release your anonymized topic?": "consent_release",
            "Do you want to be listed as co-author of the bundled dataset?": "consent_coauthor",
        },
        inplace=True,
    )
    df["timestamp"] = to_datetime(df["timestamp"])

    # Consent to release data:
    df["consent_release"] = (
        df["consent_release"]
        .map(
            {
                "Yes": True,
                "No": False,
            },
        )
        .fillna(False)
    )

    # Consent to appear as co-author of dataset:
    df["consent_coauthor"] = (
        df["consent_coauthor"]
        .map(
            {
                "Yes": True,
                "No": False,
            }
        )
        .fillna(False)
    )

    # Normalize strings.
    df["title"] = df["title"].str.strip()
    df["description"] = df["description"].str.strip()
    df["narrative"] = df["narrative"].str.strip()
    df["author"] = df["author"].str.strip()
    df["group"] = df["group"].str.strip()
    df["university"] = df["university"].str.strip()

    # Sort by submission timestamp.
    df.sort_values("timestamp", inplace=True)
    # And number the topics.
    df["number"] = range(1, len(df) + 1)

    # Anonymize for release.
    if release:
        df = df[df["consent_release"]]
        if coauthors_path is not None:
            coauthors = df.loc[df["consent_coauthor"], "author"].sort_values().unique()
            with coauthors_path.open("wt") as file:
                file.writelines(f"{author}\n" for author in coauthors)
        df.drop(columns=["author", "group", "university"], inplace=True)
    elif coauthors_path is not None:
        warn("Not exporting coauthors as release is disabled.")

    # Drop consent columns.
    df.drop(columns=["consent_release"], inplace=True)
    df.drop(columns=["consent_coauthor"], inplace=True)

    # Drop submission timestamps.
    df.drop(columns=["timestamp"], inplace=True)

    df["relevant_docnos"] = [
        _chatnoir_cache_urls_to_docnos(*urls.values)
        for _, urls in tqdm(
            df[[f"relevant_chatnoir_url_{i}" for i in (1, 2, 3)]].iterrows(),
            total=len(df),
        )
    ]
    df.drop(columns=[f"relevant_chatnoir_url_{i}" for i in (1, 2, 3)], inplace=True)
    df["irrelevant_docnos"] = [
        _chatnoir_cache_urls_to_docnos(*urls.values)
        for _, urls in tqdm(
            df[[f"irrelevant_chatnoir_url_{i}" for i in (1, 2, 3)]].iterrows(),
            total=len(df),
        )
    ]
    df.drop(columns=[f"irrelevant_chatnoir_url_{i}" for i in (1, 2, 3)], inplace=True)

    df.to_xml(
        topics_path,
        root_name="topics",
        row_name="topic",
        index=False,
        attr_cols=["number"],
        elem_cols=set(df.columns) - {"number"},
    )


@cli.command()
@argument(
    "topics_path",
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
    "pooling_path",
    type=PathType(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@option(
    "--retrieval-index",
    type=str,
    default="msmarco-passage-v2.1",
    help="The ChatNoir index to retrieve from.",
)
@option(
    "--feedback-index",
    default="msmarco-document-v2.1",
    type=str,
    help="The ChatNoir index from which feedback-documents are labeled.",
)
@option(
    "--corpus-offset",
    type=int,
    default=1500,
    help="The offset for the corpus.",
)
@option(
    "--pooling-depth",
    type=int,
    default=10,
    help="Pooling depth.",
)
def pool_documents(
    topics_path: Path,
    pooling_path: Path,
    retrieval_index: str,
    feedback_index: str,
    corpus_offset: int,
    pooling_depth: int,
) -> None:
    """
    Create top-k pools of documents retrieved by TIREx baselines using ChatNoir.
    """
    from cli.tirex import pool_documents

    pool_documents(
        topics_path=topics_path,
        pooling_path=pooling_path,
        retrieval_index=retrieval_index,
        feedback_index=feedback_index,
        corpus_offset=corpus_offset,
        pooling_depth=pooling_depth,
    )


def _user_name(project_prefix: str, group: str) -> str:
    group = slugify(group)
    return f"{project_prefix}-{group}"


_ProjectName: TypeAlias = Annotated[str, Len(min_length=1, max_length=100)]


def _project_name(project_prefix: str, query_id: str) -> _ProjectName:
    name = f"{project_prefix}-{query_id}"
    if len(query_id) == 0:
        raise ValueError("Empty query ID.")
    if len(name) > 100:
        warn(
            UserWarning(
                f"Project name '{name}' is too long. Shortening to '{name[:100]}'."
            )
        )
    return name[:100]


_alphabet = ascii_letters + digits


def _generate_password(length: int = 10) -> str:
    password = ""
    for _ in range(length):
        password += "".join(choice(_alphabet))
    return password


_DEFAULT_PROJECT_DESCRIPTION = """
Document relevance judgments. (Automatically generated by TIREx.)
""".strip()


_TAG = "teaching-ir"  # For marking auto-generated projects.
_GUIDELINES_SUFFIX = """

(This project was automatically generated by [TIREx](https://github.com/tira-io/teaching-ir-with-shared-tasks).)
""".strip()
_LABEL_RELEVANT = "relevant"
_LABEL_KEY_RELEVANT = "1"
_LABEL_COLOR_RELEVANT = "#086F02"
_LABEL_NOT_RELEVANT = "not relevant"
_LABEL_KEY_NOT_RELEVANT = "2"
_LABEL_COLOR_NOT_RELEVANT = "#D33115"
_SUPERVISOR_ROLE = "project_admin"
_ANNOTATOR_ROLE = "annotator"


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
    "-u",
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
@argument(
    "prefix",
    type=str,
)
@argument(
    "pool_path",
    type=PathType(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
    nargs=-1,
)
def prepare_relevance_judgments(
    doccano_url: str,
    doccano_username: str,
    doccano_password: str,
    guidelines_path: Path | None,
    extra_supervisors: Sequence[str],
    prefix: str,
    pool_path: Sequence[Path],
) -> None:
    """
    Prepare the relevance judgments on Doccano for pooled documents stored in JSON Lines files.
    This script will automatically create users and projects, and upload the pooled documents for each group.
    PREFIX is the common prefix of the generated project and user names.
    """

    if len(prefix) == 0:
        raise ValueError("Empty project prefix.")
    project_prefix = slugify(prefix)

    if len(pool_path) == 0:
        raise ValueError("Empty pool_path.")

    guidelines: str
    if guidelines_path is not None:
        with guidelines_path.open("rt") as file:
            guidelines = file.read()
    else:
        guidelines = files("cli").joinpath("guidelines.md").read_text()

    doccano = DoccanoClient(doccano_url)
    doccano.login(
        username=doccano_username,
        password=doccano_password,
    )
    echo("Successfully authenticated with Doccano API.")
    pool = concat(
        read_json(
            open(path, "r"),
            lines=True,
            dtype={
                "group": str,
                "query_id": str,
                "query": str,
                "description": str,
                "narrative": str,
                "doc_id": str,
                "text": str,
            },
        )
        for path in tqdm(
            pool_path,
            desc="Read pooled documents",
            unit="path",
        )
    )
    echo(f"Found {len(pool)} pooled documents.")

    groups: set[str] = set(pool["group"].drop_duplicates().to_list())
    echo(f"Found {len(groups)} groups:" + str(groups))

    # Create mapping of groups to usernames and project names.
    group_user_names: Mapping[str, str] = {
        group: _user_name(project_prefix, group) for group in groups
    }
    group_project_names: Mapping[str, str] = {
        group: _project_name(project_prefix, group) for group in groups
    }

    # Create missing users.
    users: Mapping[str, User] = {user.username: user for user in doccano.search_users()}
    group_users: dict[str, User] = {
        group: users[user_name]
        for group, user_name in group_user_names.items()
        if user_name in users.keys()
    }
    echo(f"Found {len(group_users)} existing users.")
    non_existing_group_user_names: Mapping[str, str] = {
        group: user_name
        for group, user_name in group_user_names.items()
        if user_name not in users.keys()
    }
    if len(non_existing_group_user_names) > 0:
        echo(f"Creating {len(non_existing_group_user_names)} missing users...")
        for group, user_name in non_existing_group_user_names.items():
            password = _generate_password()
            new_user = doccano.create_user(
                username=user_name,
                password=password,
            )
            group_users[group] = new_user
            echo(f"Created user '{user_name}' with password '{password}'.")

    # Create missing projects.
    projects: Mapping[str, Project] = {
        project.name: project for project in doccano.list_projects()
    }
    group_projects: dict[str, Project] = {
        group: projects[project_name]
        for group, project_name in group_project_names.items()
        if project_name in projects.keys()
    }
    echo(f"Found {len(group_projects)} existing projects.")
    unmanaged_group_projects: Mapping[str, Project] = {
        group: project
        for group, project in group_projects.items()
        if _TAG not in project.tags
    }
    if len(unmanaged_group_projects) > 0:
        echo(
            f"Checking {len(unmanaged_group_projects)} previously unmanaged projects..."
        )
        for project in unmanaged_group_projects.values():
            project_url = urljoin(doccano_url, f"/projects/{project.id}")
            confirm(
                f"The Doccano project '{project.name}' ({project_url}) does not appear to be generated by this tool. Overwrite the project",
                abort=True,
            )
    if len(group_projects) > 0:
        echo(f"Updating {len(group_projects)} existing projects...")
        for group, project in group_projects.items():
            project_id = project.id
            doccano.project.update(
                project_id=project_id,
                name=project.name,
                description=_DEFAULT_PROJECT_DESCRIPTION,
                project_type="DocumentClassification",
                guideline=f"{guidelines}{_GUIDELINES_SUFFIX}",
                random_order=False,
                collaborative_annotation=True,
                single_class_classification=True,
                tags=[_TAG],
            )
            echo(f"Updated project '{project.name}'.")
    non_existing_group_project_names: Mapping[str, str] = {
        group: project_name
        for group, project_name in group_project_names.items()
        if project_name not in projects.keys()
    }
    if len(non_existing_group_project_names) > 0:
        echo(f"Creating {len(non_existing_group_project_names)} missing projects...")
        for group, project_name in non_existing_group_project_names.items():
            new_project = doccano.project.create(
                name=project_name,
                description=_DEFAULT_PROJECT_DESCRIPTION,
                project_type="DocumentClassification",
                guideline=f"{guidelines}{_GUIDELINES_SUFFIX}",
                random_order=False,
                collaborative_annotation=True,
                single_class_classification=True,
                tags=[_TAG],
            )
            group_projects[group] = new_project
            echo(f"Created project '{project_name}'.")

    echo(f"Preparing {len(group_projects)} projects...")
    current_user = doccano.user_details.get_current_user_details()
    for group, project in group_projects.items():
        echo(f"Preparing labels for project '{project.name}'.")
        existing_labels: Sequence[LabelType] = doccano.list_label_types(
            project_id=project.id,
            type="category",
        )
        compatible_label_ids: list[int] = []
        label_relevant: LabelType | None = next(
            (label for label in existing_labels if label.text == _LABEL_RELEVANT), None
        )
        if label_relevant is not None:
            doccano.update_label_type(
                project_id=project.id,
                label_type_id=label_relevant.id,
                type="category",
                text=_LABEL_RELEVANT,
                prefix_key=None,
                suffix_key=_LABEL_KEY_RELEVANT,
                color=_LABEL_COLOR_RELEVANT,
            )
            compatible_label_ids.append(label_relevant.id)
        else:
            doccano.create_label_type(
                project_id=project.id,
                type="category",
                text=_LABEL_RELEVANT,
                prefix_key=None,
                suffix_key=_LABEL_KEY_RELEVANT,
                color=_LABEL_COLOR_RELEVANT,
            )
        label_not_relevant: LabelType | None = next(
            (label for label in existing_labels if label.text == _LABEL_NOT_RELEVANT),
            None,
        )
        if label_not_relevant is not None:
            doccano.update_label_type(
                project_id=project.id,
                label_type_id=label_not_relevant.id,
                type="category",
                text=_LABEL_NOT_RELEVANT,
                prefix_key=None,
                suffix_key=_LABEL_KEY_NOT_RELEVANT,
                color=_LABEL_COLOR_NOT_RELEVANT,
            )
            compatible_label_ids.append(label_not_relevant.id)
        else:
            doccano.create_label_type(
                project_id=project.id,
                type="category",
                text=_LABEL_NOT_RELEVANT,
                prefix_key=None,
                suffix_key=_LABEL_KEY_NOT_RELEVANT,
                color=_LABEL_COLOR_NOT_RELEVANT,
            )
        incompatible_label_ids: Sequence[int] = [
            label.id
            for label in existing_labels
            if label.id not in compatible_label_ids
        ]
        if len(incompatible_label_ids) > 0:
            confirm(
                f"Found {len(incompatible_label_ids)} incompatible labels "
                f"for project '{project}'. Delete labels",
                abort=True,
            )
            doccano.bulk_delete_label_types(
                project_id=project_id,
                label_type_ids=incompatible_label_ids,
                type="category",
            )

        echo(f"Preparing annotators for project '{project.name}'.")
        existing_members: Sequence[Member] = doccano.list_members(project_id=project.id)
        compatible_member_ids: list[int] = []
        member_user_names_roles = {
            group_user_names[group]: _ANNOTATOR_ROLE,
            **{
                user_name: _SUPERVISOR_ROLE
                for user_name in (current_user.username, *extra_supervisors)
            },
        }
        for user_name, role in member_user_names_roles.items():
            member: Member | None = next(
                (member for member in existing_members if member.username == user_name),
                None,
            )
            if member is not None:
                doccano.update_member(
                    project_id=project.id,
                    member_id=member.id,
                    role_name=role,
                )
                compatible_member_ids.append(member.id)
            else:
                doccano.add_member(
                    project_id=project.id,
                    username=user_name,
                    role_name=role,
                )
        incompatible_members: Sequence[Member] = [
            member
            for member in existing_members
            if member.id not in compatible_member_ids
        ]
        if len(incompatible_members) > 0:
            echo(f"Found {len(incompatible_members)} additional project members.")
            for member in incompatible_members:
                if confirm(f"Delete member '{member.username}'"):
                    doccano.delete_member(
                        project_id=project_id,
                        member_id=member.id,
                    )

        echo(f"Preparing data for project '{project.name}'.")
        existing_documents_count = doccano.count_examples(project_id=project.id)
        if existing_documents_count > 0:
            label_distributions = doccano.get_label_distribution(
                project_id=project.id,
                type="category",
            )
            user_label_counts = {
                distribution.username: sum(count.count for count in distribution.counts)
                for distribution in label_distributions
            }
            user_label_counts = {
                user_name: count
                for user_name, count in user_label_counts.items()
                if count > 0
            }
            if len(user_label_counts) > 0:
                user_label_counts_string = ", ".join(
                    f"user '{user_name}': {count} annotations"
                    for user_name, count in user_label_counts.items()
                )
                confirm(
                    f"Found {existing_documents_count} previous documents with {sum(user_label_counts.values())} annotations from {len(user_label_counts.keys())} users ({user_label_counts_string}). Delete documents and annotations",
                    abort=True,
                )
            else:
                confirm(
                    f"Found {existing_documents_count} previous documents without annotations. Delete documents",
                    abort=True,
                    default=True,
                )
            doccano.bulk_delete_examples(
                project_id=project.id,
                example_ids=[],  # Delete all.
            )
            # TODO: Instead update existing data and migrate annotations?

        group_pool = pool[pool["group"] == group].copy()
        if "label" not in group_pool.columns:
            group_pool["label"] = group_pool["query"].map(lambda i: [])
        echo(f"Uploading {len(group_pool)} documents to project '{project.name}'...")
        with NamedTemporaryFile() as tmp_file:
            tmp_path = Path(tmp_file.name)
            group_pool.to_json(
                tmp_path,
                orient="records",
                lines=True,
                mode="w",
            )
            tmp_file.flush()
            status = doccano.data_import.upload(
                project_id=project.id,
                file_paths=[str(tmp_path)],
                task=DataUploadTask.DOCUMENT_CLASSIFICATION,
                format="JSONL",
                column_data="text",
                column_label="label",
            )
        if not status.ready:
            raise RuntimeError(
                f"Failed to upload documents to project '{project.name}'."
            )
        error = status.error
        result = status.result
        if error is None and result is not None and "error" in result:
            error = result.pop("error")
        if error is not None and error != []:
            raise RuntimeError(
                f"Failed to upload documents to project '{project.name}': {error}"
            )
        if result is not None and result != {} and result != []:
            echo(
                f"Uploaded {len(group_pool)} documents to project '{project.name}': {status.result}"
            )
        else:
            echo(f"Uploaded {len(group_pool)} documents to project '{project.name}'.")


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
    "-u",
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
    "pooled_documents_paths",
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
    nargs=-1,
)
@argument(
    "qrels_path",
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
def export_relevance_judgments(
    doccano_url: str,
    doccano_username: str,
    doccano_password: str,
    prefix: str,
    pooled_documents_paths: Sequence[Path],
    qrels_path: Path,
) -> None:
    """
    Export the relevance judgments from Doccano for pooled documents from JSON Lines files specified in POOLED_DOCUMENTS_PATHS.
    The relevance judgments will be saved in the TREC qrels format to QRELS_PATH.
    PREFIX is the common prefix of the generated project and user names.
    """

    if len(prefix) == 0:
        raise ValueError("Empty project prefix.")
    project_prefix = slugify(prefix)

    if len(pooled_documents_paths) == 0:
        return

    doccano = DoccanoClient(doccano_url)
    doccano.login(
        username=doccano_username,
        password=doccano_password,
    )
    echo("Successfully authenticated with Doccano API.")

    pool = concat(
        read_json(
            path,
            lines=True,
            dtype={
                "group": str,
                "query_id": str,
                "query": str,
                "description": str,
                "narrative": str,
                "doc_id": str,
                "text": str,
            },
        )
        for path in tqdm(
            pooled_documents_paths,
            desc="Read pooled documents",
            unit="path",
        )
    )
    echo(f"Found {len(pool)} pooled documents.")

    groups: set[str] = set(pool["group"].drop_duplicates().to_list())
    echo(f"Found {len(groups)} groups.")

    # Create mapping of groups to project names.
    group_project_names: Mapping[str, str] = {
        group: _project_name(project_prefix, group) for group in groups
    }
    projects: Mapping[str, Project] = {
        project.name: project for project in doccano.list_projects()
    }
    group_projects: Sequence[Project] = [
        projects[project_name]
        for group, project_name in group_project_names.items()
        if project_name in projects.keys()
    ]

    echo(f"Exporting qrels from {len(group_projects)} projects...")
    qrels_list: list[DataFrame] = []
    for project in group_projects:
        with TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)

            echo(f"Downloading documents from project '{project.name}'...")
            tmp_path: Path
            retries = 10
            while True:
                try:
                    tmp_path = doccano.data_export.download(
                        project_id=project.id,
                        format="JSONL",
                        dir_name=str(tmp_dir_path),
                    )
                except DoccanoAPIError as e:
                    # Note: These errors are so common in Doccano, that a warning does not seem appropriate.
                    if e.response.status_code != 500 or retries <= 0:
                        raise e
                    echo(
                        f"Re-trying documents download from project '{project.name}'. {retries} retries left."
                    )
                    retries -= 1
                    continue
                break

            echo(f"Downloaded documents from project '{project.name}'.")

            with ZipFile(tmp_path) as tmp_zip_file:
                for name in tmp_zip_file.namelist():
                    with tmp_zip_file.open(name) as tmp_jsonl_file:
                        qrels_list.append(
                            read_json(
                                tmp_jsonl_file,
                                lines=True,
                                dtype={
                                    "query_id": str,
                                    "doc_id": str,
                                },
                            )[["query_id", "doc_id", "label"]]
                        )

    echo("Read qrels from annotated documents.")
    qrels = concat(qrels_list)
    qrels["label"] = qrels["label"].map(lambda x: x[0] if len(x) > 0 else None)
    qrels = qrels[qrels["label"].notna()]
    qrels["label"] = qrels["label"].map(
        {
            _LABEL_RELEVANT: 1,
            _LABEL_NOT_RELEVANT: 0,
        }
    )
    qrels = qrels[qrels["label"].notna()]

    pool = pool.merge(
        qrels,
        how="left",
        on=["query_id", "doc_id"],
        suffixes=["_pool", None],
    )
    unjudged_pool = pool[pool["label"].isna()]
    if len(unjudged_pool) > 0:
        echo(f"Found {len(unjudged_pool)} unjudged documents from pool.")
        if confirm("Report unjudged documents", default=True):
            for group, group_unjudged_pool in unjudged_pool.groupby("group"):
                echo(
                    f"\tGroup '{group}': {len(group_unjudged_pool)} unjudged documents."
                )

    echo(f"Export qrels file to {qrels_path}.")
    qrels["Q0"] = 0
    qrels = qrels[["query_id", "Q0", "doc_id", "label"]]
    qrels.to_csv(
        qrels_path,
        sep=" ",
        index=False,
        header=False,
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
    "-u",
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

    if len(prefix) == 0:
        raise ValueError("Empty project prefix.")

    doccano = DoccanoClient(doccano_url)
    doccano.login(
        username=doccano_username,
        password=doccano_password,
    )
    echo("Successfully authenticated with Doccano API.")

    # Clean up projects.
    projects: Sequence[Project] = [
        project
        for project in doccano.list_projects()
        if project.name.startswith(prefix) and _TAG in project.tags
    ]
    if len(projects) > 0:
        bulk_delete_projects = confirm(f"Found {len(projects)} projects. Bulk delete")
        for project in projects:
            if not bulk_delete_projects:
                confirm(f"Delete project '{project.name}'", abort=True)
            doccano.project.delete(project_id=project.id)
            echo(message=f"Deleted project '{project.name}'.")

    # Clean up users (semi-automatically).
    users: Sequence[User] = [
        user for user in doccano.search_users() if user.username.startswith(prefix)
    ]
    if len(users) > 0:
        auto_open_delete_urls = confirm(
            f"Found {len(projects)} users. Users can only be deleted semi-automatically. Open browser tabs to confirm user deletions"
        )
        for user in users:
            delete_user_url = urljoin(
                doccano_url, f"/admin/auth/user/{user.id}/delete/"
            )

            if auto_open_delete_urls:
                open_webbrowser(delete_user_url)
            else:
                confirm(
                    f"Delete user '{user.username}' at {delete_user_url}",
                    default=True,
                    show_default=False,
                    prompt_suffix=". Press enter to continue.",
                )


if __name__ == "__main__":
    # pylint: disable=E1120
    cli()
