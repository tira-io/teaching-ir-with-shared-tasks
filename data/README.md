# Data

This directory organizes the data used to create the corpora, mainly for pooling.

## How-To

For each new corpus respectively IR course, create a new directory and add the topics.xml file there, i.e.:

- <new-course>/topics.xml

# ln -s /mnt/ceph/storage/corpora/corpora-thirdparty/corpus-msmarco-v2.1-document-retrieval/msmarco_v2.1_doc_segmented ~/.ir_datasets/msmarco-segment-v2.1/msmarco_v2.1_doc_segmented.tar.extracted
Then, run `./pooling.py <new-course>` to create all additional data.



