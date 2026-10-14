from pathlib import Path

from yaml import safe_load_all  # type: ignore[import-untyped]

from cli.chatnoir_docker import (
    container_name_for,
    discover_corpora,
    kubernetes_manifest,
    network_name_for,
)


def test_container_and_network_name() -> None:
    container_name = container_name_for(Path("/ceph/courses/IR WiSe 2026"))
    assert container_name == "chatnoir-ir-wise-2026"
    assert network_name_for(container_name) == "chatnoir-ir-wise-2026-net"


def test_discover_corpora(tmp_path: Path) -> None:
    named = tmp_path / "My Corpus"
    named.mkdir()
    (named / "documents.jsonl").write_text("{}\n")
    (named / "metadata.yml").write_text("dataset:\n  name: My Nice Corpus\n")

    unnamed = tmp_path / "other-corpus"
    unnamed.mkdir()
    (unnamed / "documents.jsonl").write_text("{}\n")

    # Ignored: no documents.jsonl, or not a directory.
    (tmp_path / "empty").mkdir()
    (tmp_path / "documents.jsonl").write_text("{}\n")

    corpora = discover_corpora(tmp_path)

    assert [corpus.directory for corpus in corpora] == [named, unnamed]
    assert [corpus.corpus_id for corpus in corpora] == ["my_corpus", "other_corpus"]
    assert corpora[0].meta_index == "chatnoir_meta_my_corpus"
    assert corpora[0].data_index == "chatnoir_data_my_corpus"
    assert [corpus.display_name for corpus in corpora] == [
        "My Nice Corpus",
        "other_corpus",
    ]


def test_discover_corpora_invalid_metadata(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "documents.jsonl").write_text("{}\n")
    (corpus / "metadata.yml").write_text("dataset: [unclosed\n")

    corpora = discover_corpora(tmp_path)

    assert [c.display_name for c in corpora] == ["corpus"]


def test_kubernetes_manifest() -> None:
    manifest = kubernetes_manifest(
        course_name="WiSe 2026",
        image_tag="ghcr.io/example/chatnoir:wise-2026-latest",
        namespace="demos",
        hostname_pattern="{course}.example.com",
        cache_hostname_pattern="{course}-cache.example.com",
    )

    deployment, service, ingress = safe_load_all(manifest)

    assert deployment["kind"] == "Deployment"
    assert deployment["metadata"]["name"] == "chatnoir-wise-2026"
    assert deployment["metadata"]["namespace"] == "demos"
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == "ghcr.io/example/chatnoir:wise-2026-latest"
    startup_script = container["args"][0]
    assert "https://wise-2026.example.com/" in startup_script
    assert "https://wise-2026-cache.example.com/" in startup_script

    assert service["kind"] == "Service"
    assert [port["port"] for port in service["spec"]["ports"]] == [8000, 8001]

    assert ingress["kind"] == "Ingress"
    assert [
        (rule["host"], rule["http"]["paths"][0]["backend"]["service"]["port"]["number"])
        for rule in ingress["spec"]["rules"]
    ] == [
        ("wise-2026.example.com", 8000),
        ("wise-2026-cache.example.com", 8001),
    ]
