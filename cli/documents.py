"""
Conversion of document collections submitted via Google Forms (exported as
CSV) to a `documents/` directory, with one sub-directory (containing
`documents.jsonl` and `metadata.yml`) per submitted collection plus a merged
`documents.jsonl` and `metadata.yml` for the joined collection.
"""

from json import JSONDecodeError, dumps, loads
from pathlib import Path
from re import compile as re_compile
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlparse
from warnings import warn

from click import echo
from pandas import DataFrame, isna, read_csv, to_datetime
from requests import RequestException, session
from slugify import slugify
from tqdm import tqdm
from yaml import SafeDumper, safe_dump  # type: ignore[import-untyped]

_session = session()

_DOWNLOAD_CACHE_PATH = Path(".drive_cache")
_DRIVE_DOWNLOAD_URL = "https://drive.usercontent.google.com/download"
_DRIVE_FILE_PATH_PATTERN = re_compile(r"/file/d/([^/]+)")
_SEPARATOR_PATTERN = re_compile(r"[\s,;]+")
# Google Sheets exports timestamps like "2026/10/12 3:11:22 PM OESZ" or
# "12.10.2026 15:11:22", depending on the locale.
_TIMESTAMP_FORMATS = ("%Y/%m/%d %I:%M:%S %p", "%d.%m.%Y %H:%M:%S")
_REQUIRED_FIELDS = ("docno", "url", "title", "text")


def _str_representer(dumper: SafeDumper, data: str) -> Any:
    # Use YAML block style for multi-line strings, as in the example metadata.
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


# FIXME: Do not modify this globally, just in the function where it is needed.
SafeDumper.add_representer(str, _str_representer)


def _parse_timestamp(timestamp: str) -> Any:
    # Strip trailing time zone abbreviations (e.g., "OESZ"), not parseable.
    parts = timestamp.strip().split(" ")
    if parts[-1].isalpha() and parts[-1] not in ("AM", "PM"):
        parts = parts[:-1]
    timestamp = " ".join(parts)
    for timestamp_format in _TIMESTAMP_FORMATS:
        try:
            return to_datetime(timestamp, format=timestamp_format)
        except ValueError:
            continue
    raise ValueError(f"Could not parse timestamp: {timestamp}")


def _split(value: Any) -> list[str]:
    if isna(value):
        return []
    return [x for x in _SEPARATOR_PATTERN.split(str(value)) if x != ""]


def _drive_file_id(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "id" in query:
        return query["id"][0]
    match = _DRIVE_FILE_PATH_PATTERN.search(parsed.path)
    if match is not None:
        return match.group(1)
    return None


def _download_drive_file(url: str) -> Path:
    file_id = _drive_file_id(url)
    if file_id is None:
        raise ValueError(f"Not a Google Drive file URL: {url}")
    path = _DOWNLOAD_CACHE_PATH / file_id
    if path.exists():
        return path

    _DOWNLOAD_CACHE_PATH.mkdir(parents=True, exist_ok=True)
    response = _session.get(
        _DRIVE_DOWNLOAD_URL,
        params={"id": file_id, "export": "download", "confirm": "t"},
        stream=True,
        timeout=60,
    )
    response.raise_for_status()
    if response.headers.get("Content-Type", "").startswith("text/html"):
        raise RequestException(
            f"Could not download file from Google Drive (is it shared publicly?): {url}"
        )
    temp_path = path.with_suffix(".part")
    with temp_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)
    temp_path.rename(path)
    return path


def _read_documents(paths: Iterable[Path]) -> Iterable[Mapping[str, Any]]:
    for path in paths:
        with path.open("rt", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if line.strip() == "":
                    continue
                try:
                    document = loads(line)
                except JSONDecodeError:
                    warn(f"Skipping invalid JSON in {path}:{line_number}.")
                    continue
                missing = [field for field in _REQUIRED_FIELDS if field not in document]
                if len(missing) > 0:
                    warn(
                        f"Skipping document in {path}:{line_number} "
                        f"with missing fields: {', '.join(missing)}."
                    )
                    continue
                yield document


def _metadata(row: Mapping[Any, Any], release: bool) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if not release:
        metadata["authors"] = [{
            "name": row["author"],
            "group": row["group"],
            "university": row["university"],
        }]
        metadata["copyright"] = {
            "consentRelease": row["consent_release"],
            "consentCoauthor": row["consent_coauthor"],
        }
    crawler: dict[str, Any] = {
        "seedUrls": row["seed_urls"],
    }
    if row["filtering"] != "":
        crawler["filtering"] = row["filtering"]
    metadata["dataset"] = {
        "id": row["id"],
        "name": row["title"],
        "description": row["description"],
        "crawler": crawler,
    }
    return metadata


def _merged_metadata(
    df: DataFrame,
    dataset_id: str,
    name: str,
    description: str,
    release: bool,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if not release:
        metadata["authors"] = [
            {
                "name": row["author"],
                "group": row["group"],
                "university": row["university"],
            }
            for _, row in df.iterrows()
        ]
    metadata["copyright"] = {
        "consentRelease": bool(df["consent_release"].all()),
        "consentCoauthor": None,
    }
    seed_urls = list(dict.fromkeys(url for urls in df["seed_urls"] for url in urls))
    metadata["dataset"] = {
        "id": dataset_id,
        "name": name,
        "description": description,
        "crawler": {
            "seedUrls": seed_urls,
        },
    }
    return metadata


def _write_metadata(metadata: Mapping[str, Any], path: Path) -> None:
    with path.open("wt", encoding="utf-8") as file:
        safe_dump(
            metadata,
            file,
            sort_keys=False,
            allow_unicode=True,
        )


def _write_documents(documents: Iterable[Mapping[str, Any]], path: Path) -> int:
    """
    Write documents to a JSONL file, skipping documents with duplicate docnos.
    Returns the number of written documents.
    """
    docnos: set[str] = set()
    num_duplicates = 0
    with path.open("wt", encoding="utf-8") as file:
        for document in documents:
            if document["docno"] in docnos:
                num_duplicates += 1
                continue
            docnos.add(document["docno"])
            file.write(dumps(document) + "\n")
    if num_duplicates > 0:
        warn(f"Skipped {num_duplicates} documents with duplicate docnos in '{path}'.")
    return len(docnos)


def convert_documents_csv(
    csv_path: Path,
    documents_path: Path,
    dataset_id: str = "documents",
    name: str = "Merged Document Collection",
    description: str = "Merged collection of all submitted document collections.",
    release: bool = False,
    coauthors_path: Path | None = None,
    from_date: str | None = None,
    filter_university: str | None = None,
) -> None:
    """
    Convert a document collections spread sheet exported from Google Forms as
    CSV to a documents directory with individual and merged collections.
    """
    df = read_csv(csv_path, dtype=str, keep_default_na=False)
    df.rename(
        columns={
            "Zeitstempel": "timestamp",
            "Title": "title",
            "Description": "description",
            "Seed URLs": "seed_urls",
            "Additional filtering/post-processing": "filtering",
            "Document collection": "collection_urls",
            "Full name": "author",
            "Group name": "group",
            "University": "university",
            "Do you consent to release your anonymized document collection?": "consent_release",
            "Do you want to be listed as co-author of the bundled dataset?": "consent_coauthor",
        },
        inplace=True,
    )
    df["timestamp"] = df["timestamp"].map(_parse_timestamp)

    # Normalize strings.
    for column in (
        "title",
        "description",
        "filtering",
        "author",
        "group",
        "university",
        "consent_release",
        "consent_coauthor",
    ):
        df[column] = df[column].str.strip()
    df["seed_urls"] = df["seed_urls"].map(_split)
    df["collection_urls"] = df["collection_urls"].map(_split)

    # Sort by submission timestamp.
    df.sort_values("timestamp", inplace=True)

    # Consent to release data:
    df["consent_release"] = df["consent_release"] == "Yes"

    # Consent to appear as co-author of dataset:
    df["consent_coauthor"] = df["consent_coauthor"] == "Yes"

    echo(f"Found {len(df)} document collections.")

    # Remove empty submissions.
    df = df.loc[df["title"] != ""]
    df = df.loc[df["collection_urls"].map(len) > 0]

    # Filter by submission date.
    if from_date is not None:
        from_date_parsed = to_datetime(from_date, format="%Y-%m-%d", errors="raise")
        df = df[df["timestamp"] >= from_date_parsed]
        echo(
            f"Filtered document collections from date {from_date_parsed.date()}: "
            f"{len(df)} document collections remain."
        )

    # Filter by university.
    if filter_university is not None:
        df = df[df["university"] == filter_university]
        echo(
            f"Filtered document collections from university '{filter_university}': "
            f"{len(df)} document collections remain."
        )

    # Filter by consent for release.
    if release:
        df = df[df["consent_release"]]
        if coauthors_path is not None:
            coauthors = df.loc[df["consent_coauthor"], "author"].sort_values().unique()
            with coauthors_path.open("wt") as file:
                file.writelines(f"{author}\n" for author in coauthors)
    elif coauthors_path is not None:
        warn("Not exporting co-authors as release is disabled.")

    # Assign unique, readable IDs based on the collection titles.
    ids: list[str] = []
    for title in df["title"]:
        base_id = slugify(title)
        collection_id = base_id
        suffix = 2  # Append `-2` and so on, if the ID is already present.
        while collection_id in ids or collection_id == dataset_id:
            collection_id = f"{base_id}-{suffix}"
            suffix += 1
        ids.append(collection_id)
    df["id"] = ids

    documents_path.mkdir(parents=True, exist_ok=True)
    exported_ids: list[str] = []
    for _, row in tqdm(
        df.iterrows(),
        total=len(df),
        desc="Convert document collections",
        unit="collection",
    ):
        try:
            downloaded_paths = [
                _download_drive_file(url) for url in row["collection_urls"]
            ]
        except (RequestException, ValueError) as error:
            warn(f"Skipping document collection '{row['id']}': {error}")
            continue

        collection_path = documents_path / row["id"]
        collection_path.mkdir(parents=True, exist_ok=True)
        num_documents = _write_documents(
            _read_documents(downloaded_paths),
            collection_path / "documents.jsonl",
        )
        _write_metadata(
            _metadata(row.to_dict(), release),
            collection_path / "metadata.yml",
        )
        exported_ids.append(row["id"])
        echo(f"Wrote {num_documents} documents to '{collection_path}'.")

    merged_documents_path = documents_path / "documents.jsonl"
    num_merged_documents = _write_documents(
        _read_documents(
            documents_path / collection_id / "documents.jsonl"
            for collection_id in exported_ids
        ),
        merged_documents_path,
    )

    df = df[df["id"].isin(exported_ids)]
    _write_metadata(
        _merged_metadata(df, dataset_id, name, description, release),
        documents_path / "metadata.yml",
    )
    echo(
        f"Wrote {num_merged_documents} documents from {len(df)} document collections "
        f"to '{merged_documents_path}'."
    )
