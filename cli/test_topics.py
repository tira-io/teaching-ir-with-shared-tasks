from pathlib import Path
from typing import Any

from pandas import DataFrame, read_xml
from pytest import MonkeyPatch, fixture, warns

from cli import topics
from cli.topics import _chatnoir_cache_urls_to_docnos, convert_topics_csv_to_xml

_COLUMNS = (
    "Zeitstempel",
    "Title",
    "Description",
    "Narrative",
    "Relevant document #1",
    "Relevant document #2",
    "Relevant document #3",
    "Irrelevant document #1",
    "Irrelevant document #2",
    "Irrelevant document #3",
    "Full name",
    "Group name",
    "University",
    "Do you consent to release your anonymized topic?",
    "Do you want to be listed as co-author of the bundled dataset?",
)


def _row(
    timestamp: str,
    title: str,
    author: str,
    university: str = "Jena",
    consent_release: str = "Yes",
    consent_coauthor: str = "Yes",
) -> tuple[str, ...]:
    return (
        timestamp,
        f" {title} ",
        f"Description of {title}",
        f"Narrative of {title}",
        f"https://chatnoir.example/cache?uuid={title}-rel-1",
        f"https://chatnoir.example/cache?uuid={title}-rel-2",
        "",
        f"https://chatnoir.example/cache?uuid={title}-irrel-1",
        "",
        "",
        author,
        f"Team {author}",
        university,
        consent_release,
        consent_coauthor,
    )


@fixture
def csv_path(tmp_path: Path) -> Path:
    path = tmp_path / "topics.csv"
    DataFrame(
        [
            _row("02.11.2026 10:00:00", "second", "Bob", consent_coauthor="No"),
            _row("01.11.2026 10:00:00", "first", "Alice"),
            _row("03.11.2026 10:00:00", "third", "Carol", university="Kassel"),
            _row("04.11.2026 10:00:00", "private", "Dave", consent_release="No"),
            _row("05.11.2026 10:00:00", "", "Eve"),
        ],
        columns=list(_COLUMNS),
    ).to_csv(path, index=False)
    return path


@fixture(autouse=True)
def fake_chatnoir(monkeypatch: MonkeyPatch) -> None:
    # Resolve "cache URLs" locally instead of requesting ChatNoir.
    def _fake(url: str) -> str | None:
        return url.split("uuid=")[-1]

    monkeypatch.setattr(topics, "_chatnoir_cache_url_to_docno", _fake)


def _read_topics(path: Path) -> DataFrame:
    return read_xml(path, dtype=str)


def test_convert_topics(csv_path: Path, tmp_path: Path) -> None:
    topics_path = tmp_path / "topics.xml"

    convert_topics_csv_to_xml(csv_path, topics_path)

    df = _read_topics(topics_path)
    # Empty topics are removed, the rest numbered by submission time.
    assert df["title"].tolist() == ["first", "second", "third", "private"]
    assert df["number"].tolist() == ["1", "2", "3", "4"]
    assert df["relevant_docnos"].tolist()[0] == "first-rel-1,first-rel-2"
    assert df["irrelevant_docnos"].tolist()[0] == "first-irrel-1"
    assert df["author"].tolist() == ["Alice", "Bob", "Carol", "Dave"]
    assert "consent_release" not in df.columns
    assert "timestamp" not in df.columns


def test_convert_topics_release(csv_path: Path, tmp_path: Path) -> None:
    topics_path = tmp_path / "topics.xml"
    coauthors_path = tmp_path / "coauthors.txt"

    convert_topics_csv_to_xml(
        csv_path, topics_path, release=True, coauthors_path=coauthors_path
    )

    df = _read_topics(topics_path)
    assert df["title"].tolist() == ["first", "second", "third"]
    # Topic numbers stay stable when filtering for consent.
    assert df["number"].tolist() == ["1", "2", "3"]
    assert {"author", "group", "university"}.isdisjoint(df.columns)
    assert coauthors_path.read_text() == "Alice\nCarol\n"


def test_convert_topics_coauthors_without_release(
    csv_path: Path, tmp_path: Path
) -> None:
    coauthors_path = tmp_path / "coauthors.txt"

    with warns(UserWarning):
        convert_topics_csv_to_xml(
            csv_path, tmp_path / "topics.xml", coauthors_path=coauthors_path
        )

    assert not coauthors_path.exists()


def test_convert_topics_filters(csv_path: Path, tmp_path: Path) -> None:
    topics_path = tmp_path / "topics.xml"

    convert_topics_csv_to_xml(
        csv_path,
        topics_path,
        from_date="2026-11-02",
        filter_university="Jena",
    )

    df = _read_topics(topics_path)
    assert df["title"].tolist() == ["second", "private"]


def test_chatnoir_cache_urls_to_docnos(monkeypatch: MonkeyPatch) -> None:
    resolved = {"a": "doc-a", "b": None, "c": "doc-c"}
    monkeypatch.setattr(topics, "_chatnoir_cache_url_to_docno", resolved.get)

    nan: Any = float("nan")
    assert _chatnoir_cache_urls_to_docnos("a", nan, "b", "c") == "doc-a,doc-c"
