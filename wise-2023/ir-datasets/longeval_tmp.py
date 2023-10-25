import ir_datasets
from ir_datasets.formats import JsonlDocs, TrecXmlQueries, TrecQrels
from typing import NamedTuple
from ir_datasets.datasets.base import Dataset

class LongEvalDocument(NamedTuple):
    doc_id: str
    url: str
    text: str

    def default_text(self):
        return self.text

ir_datasets.registry.register('longeval-tutors', Dataset(
    JsonlDocs(ir_datasets.util.PackageDataFile(path='datasets_in_progress/longeval-docs.jsonl'), doc_cls=LongEvalDocument, lang='en'),
    TrecXmlQueries(ir_datasets.util.PackageDataFile(path='datasets_in_progress/topics.xml'), lang='en'),
    TrecQrels(ir_datasets.util.PackageDataFile(path='datasets_in_progress/qrels.txt'), {0: 'Not Relevant', 1: 'Relevant'})
))
