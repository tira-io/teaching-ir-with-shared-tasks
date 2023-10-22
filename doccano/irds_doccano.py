from functools import cache
from hashlib import sha1
from json import dumps
from pathlib import Path

from click import group, option, argument, Path as PathType
from doccano_client import DoccanoClient
from tira.third_party_integrations import ir_datasets


@group
def main() -> None:
    pass


@main.command()
@option(
    "--doccano-url",
    required=True,
    default="https://doccano.web.webis.de/",
    type=str,
)
@option(
    "--doccano-username",
    required=True,
    type=str,
)
@option(
    "--doccano-password",
    required=True,
    type=str,
)
@argument(
    "irds_id",
    type=str,
)
@argument(
    "output_file_path",
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
    default=Path("project_data.jsonl"),
)
def create_projects(
        doccano_url: str,
        doccano_username: str,
        doccano_password: str,
        irds_id: str,
        output_file_path: Path,
) -> None:
    # client = _client(doccano_url, doccano_username, doccano_password)
    dataset = ir_datasets.load(irds_id)
    qrels_query_ids = {
        str(qrel.query_id)
        for qrel in dataset.qrels_iter()
    }
    print(f"Found {len(qrels_query_ids)} query IDs in qrels.")
    qrels_doc_ids = {
        str(qrel.doc_id)
        for qrel in dataset.qrels_iter()
    }
    print(f"Found {len(qrels_doc_ids)} document IDs in qrels.")
    queries = {
        str(query.query_id): query
        for query in dataset.queries_iter()
        if str(query.query_id) in qrels_query_ids
    }
    print(f"Found {len(queries)} queries.")
    docs = {
        str(doc.doc_id): doc
        for doc in dataset.docs_iter()
        if str(doc.doc_id) in qrels_doc_ids
    }
    print(f"Found {len(docs)} documents.")
    with open(output_file_path, "w") as output_file:
        for qrel in dataset.qrels_iter():
            query = queries.get(qrel.query_id)
            if query is None:
                print(f"Query {qrel.query_id} not found.")
                continue
            doc = docs.get(qrel.doc_id)
            if doc is None:
                print(f"Document {qrel.doc_id} not found.")
                continue
            item ={
                "query_id": qrel.query_id,
                "doc_id": qrel.doc_id,
                "query": query.default_text(),
                "text": doc.default_text(),
            }
            if hasattr(query, "description"):
                item["description"] = query.description
            if hasattr(query, "narrative"):
                item["narrative"] = query.narrative
            line = dumps(item)
            output_file.write(f"{line}\n")

# project_name = f"irds-{irds_id.replace('/', '-')}-topic-{query_id}"
# project_exists = _project_exists(client, project_name)
# if project_exists:
#     print(f"Project '{project_name}' already exists. Skipping.")
#     continue
# print(f"Creating project '{project_name}'")
# project = Project(
#     name=project_name,
#     project_type="DocumentClassification",
#     description=query.default_text(),
#     collaborative_annotation=True,
# )
# payload = client._project_repository._to_persistent(project)
# payload.pop("id", None)
# response = client._base_repository.post("projects", json=payload)
# response.raise_for_status()

def grouper(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i+n]

@cache
def _projects(client: DoccanoClient) -> list[dict]:
    response = client._base_repository.get("projects")
    return response.json()


def _project_exists(client: DoccanoClient, project_name: str) -> bool:
    projects = _projects(client)
    for project in projects:
        if project["name"] == project_name:
            return True
    return False


def _usernames(irds_id: str) -> list[str]:
    dataset = ir_datasets.load(irds_id)
    queries = list(dataset.queries_iter())
    qrels = dataset.qrels_dict()
    return [
        f"assessor-"
        f"dataset-{irds_id.replace('/', '-')}-"
        f"topic-{query.query_id}"
        for query in queries
        if query.query_id in qrels
    ]


def _passwords(irds_id: str) -> list[str]:
    users = _usernames(irds_id)
    return [
        sha1(user.encode("utf-8")).hexdigest()
        for user in users
    ]


def _client(doccano_url: str, doccano_username: str, doccano_password: str,
            ) -> DoccanoClient:
    client = DoccanoClient(
        base_url=doccano_url,
    )
    client.login(
        username=doccano_username,
        password=doccano_password,
    )
    return client


if __name__ == "__main__":
    main()
