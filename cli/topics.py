"""
Conversion of topics submitted via Google Forms (exported as CSV) to a
`topics.xml` file, resolving ChatNoir cache URLs to document IDs.
"""
from json import JSONDecodeError
from pathlib import Path
from warnings import warn

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from pandas import isna, read_csv, to_datetime
from requests import RequestException, session
from tqdm import tqdm

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


def convert_topics_csv_to_xml(
    csv_path: Path,
    topics_path: Path,
    release: bool = False,
    coauthors_path: Path | None = None,
    from_date: str | None = None,
    filter_university: str | None = None,
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
    df["timestamp"] = to_datetime(df["timestamp"], format="%d.%m.%Y %H:%M:%S")

    # Normalize strings.
    df["title"] = df["title"].str.strip()
    df["description"] = df["description"].str.strip()
    df["narrative"] = df["narrative"].str.strip()
    df["author"] = df["author"].str.strip()
    df["group"] = df["group"].str.strip()
    df["university"] = df["university"].str.strip()
    df["consent_release"] = df["consent_release"].str.strip()
    df["consent_coauthor"] = df["consent_coauthor"].str.strip()

    # Sort by submission timestamp.
    df.sort_values("timestamp", inplace=True)
    # And number the topics.
    df["number"] = range(1, len(df) + 1)

    # Consent to release data:
    df["consent_release"] = df["consent_release"].map(
        lambda x: True if x == "Yes" else False
    )

    # Consent to appear as co-author of dataset:
    df["consent_coauthor"] = df["consent_coauthor"].map(
        lambda x: True if x == "Yes" else False
    )

    print(f"Found {len(df)} topics.")

    # Remove empty topics.
    df = df.loc[(df["title"] != "") & df["title"].notna()]
    df = df.loc[(df["description"] != "") & df["description"].notna()]
    df = df.loc[(df["narrative"] != "") & df["narrative"].notna()]

    # Filter by submission year.
    if from_date is not None:
        from_date_parsed = to_datetime(from_date, format="%Y-%m-%d", errors="raise")
        df = df[df["timestamp"] >= from_date_parsed]
        print(f"Filtered topics from date {from_date_parsed.date()}: {len(df)} topics remain.")

    # Filter by university.
    if filter_university is not None:
        df = df[df["university"] == filter_university]
        print(f"Filtered topics from university '{filter_university}': {len(df)} topics remain.")

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
        elem_cols=sorted(set(df.columns) - {"number"}),
    )
