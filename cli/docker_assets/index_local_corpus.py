#!/usr/bin/env python3
"""
Index a local ``documents.jsonl`` corpus into ChatNoir's Elasticsearch
indices, without requiring the corpus to be registered with ir_datasets
first, and upload the corpus file as-is to the bundled MinIO/S3 instance so
that the ChatNoir cache/document view works for it too.

This script is mounted (read-only) into the *unmodified*
`chatnoir-ir-datasets-indexer` Docker image by `teaching-ir build-chatnoir`
and run in place of that image's own CLI. It monkey-patches the indexer's
internal dataset-mapping dispatch (`chatnoir_ir_datasets_indexer.index`) to
additionally recognize a local directory (containing a `documents.jsonl`
file with `docno`/`url`/`title`/`text` fields per line) as a valid "dataset",
reusing all of the indexer's existing Elasticsearch indexing logic.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, NamedTuple, Optional

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from chatnoir_ir_datasets_indexer import index as _index_module


class LocalDoc(NamedTuple):
    doc_id: str
    url: Optional[str]
    title: Optional[str]
    text: str
    offset: int
    length: int


class LocalCorpusMapping(_index_module.DatasetMapping):
    num_data_shards = 1
    num_data_replicas = 0
    num_meta_shards = 1
    num_meta_replicas = 0
    base_dir = Path(".")

    def __init__(self, corpus_id: str, documents_path: Path):
        self._corpus_id = corpus_id
        self._documents_path = documents_path

    @property
    def corpus_prefix(self) -> str:
        return self._corpus_id

    def docs_count(self) -> int:
        with self._documents_path.open("rb") as file:
            return sum(1 for line in file if line.strip())

    def docs_iter(self) -> Iterator[LocalDoc]:
        with self._documents_path.open("rb") as file:
            offset = 0
            for raw_line in file:
                length = len(raw_line)
                line = raw_line.strip()
                if not line:
                    offset += length
                    continue
                record = json.loads(line)
                yield LocalDoc(
                    doc_id=str(record["docno"]),
                    url=record.get("url"),
                    title=record.get("title"),
                    text=record.get("text") or "",
                    offset=offset,
                    length=length,
                )
                offset += length

    def record_time(self, doc: LocalDoc) -> datetime:
        return datetime.now(timezone.utc)

    def warc_path(self, doc: LocalDoc) -> Path:
        return Path(self._corpus_id) / "documents.jsonl"

    def warc_offset(self, doc: LocalDoc) -> int:
        return doc.offset

    def meta_record(self, doc: LocalDoc, s3_bucket: Optional[str]):
        return _index_module.MetaRecord(
            source_file=self.warc_file(doc, s3_bucket),
            source_offset=doc.offset,
            content_length=doc.length,
            content_type="application/json",
            uuid=self.webis_id(doc),
            warc_trec_id=doc.doc_id,
        )

    def data_record(self, doc: LocalDoc):
        return _index_module.DataRecord(
            uuid=self.webis_id(doc),
            lang="en",
            warc_date=None,
            warc_record_id=None,
            warc_trec_id=doc.doc_id,
            warc_target_uri=doc.url,
            warc_target_hostname=None,
            warc_target_path=None,
            warc_target_query_string=None,
            http_date=None,
            http_content_type="text/html",
            title=doc.title or f"Document {doc.doc_id}",
            meta_keywords=None,
            meta_desc=None,
            body=doc.text,
            body_length=len(doc.text),
            full_body=doc.text,
            headings=None,
        )


def _local_mapping_for(dataset_id: str) -> Optional[LocalCorpusMapping]:
    path = Path(dataset_id)
    documents_path = path / "documents.jsonl"
    if path.is_dir() and documents_path.is_file():
        return LocalCorpusMapping(path.name, documents_path)
    return None


_original_dataset_mapping = _index_module._dataset_mapping
_original_iter_docs = _index_module._iter_docs


def _patched_dataset_mapping(dataset_id: str):
    mapping = _local_mapping_for(dataset_id)
    if mapping is not None:
        return mapping
    return _original_dataset_mapping(dataset_id)


def _patched_iter_docs(start, end, dataset_id):
    mapping = _local_mapping_for(dataset_id)
    if mapping is not None:
        total = mapping.docs_count()
        docs_iter = mapping.docs_iter()
        from tqdm.auto import tqdm
        docs_iter = tqdm(
            docs_iter,
            total=total,
            desc=f"Iterate local corpus {dataset_id}",
        )
        return docs_iter, total
    return _original_iter_docs(start, end, dataset_id)


_index_module._dataset_mapping = _patched_dataset_mapping
_index_module._iter_docs = _patched_iter_docs


def _upload_corpus_to_s3(
    corpus_dir: Path,
    corpus_id: str,
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
) -> None:
    """
    Uploads the corpus' `documents.jsonl` as-is (same bytes, so that the
    offsets computed in `docs_iter` remain valid) to the bundled MinIO/S3
    instance, so that the ChatNoir cache/document view can read it back.
    """
    client = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )
    try:
        client.head_bucket(Bucket=s3_bucket)
    except ClientError:
        client.create_bucket(Bucket=s3_bucket)
    key = f"{corpus_id}/documents.jsonl"
    client.upload_file(str(corpus_dir / "documents.jsonl"), s3_bucket, key)


if __name__ == "__main__":
    (
        _script,
        es_host,
        es_username,
        es_password,
        meta_index,
        data_index,
        dataset_dir,
        s3_endpoint,
        s3_access_key,
        s3_secret_key,
        s3_bucket,
    ) = sys.argv
    _upload_corpus_to_s3(
        Path(dataset_dir),
        Path(dataset_dir).name,
        s3_endpoint,
        s3_access_key,
        s3_secret_key,
        s3_bucket,
    )
    _index_module.index(
        es_host=es_host,
        es_username=es_username,
        es_password=es_password,
        es_index_meta=meta_index,
        es_index_data=data_index,
        s3_bucket=s3_bucket,
        start=None,
        end=None,
        dataset_id=dataset_dir,
    )

