# For teachers

The following documentation describes how to use the integrated `teaching-ir` CLI tool to automate most of the administrative tasks of the IR lab.

Please also refer to the `teaching-ir` command's help (i.e., run `teaching-ir --help`) for more detailed options.

## Installation

1. Install [Python 3](https://python.org/downloads/).
2. Create and activate a virtual environment:

    ```shell
    python3 -m venv venv/
    source venv/bin/activate
    ```

3. Install dependencies:

    ```shell
    pip install -e .
    ```

## Setting up topic submission

> TODO: Link a Google Forms template.

## Collecting and converting topics

Now, we want to export the topics from Google Forms and convert it to a machine-readable, TREC-compatible XML format.

> TODO: Describe CSV download from Google Sheets.

After having downloaded the CSV file from Google, convert the topics to an XML file like so:

```shell
teaching-ir convert-topics-csv-to-xml /path/to/topics.csv topics.xml
```

The script will convert the ChatNoir URLs back to the document IDs and assign topic IDs based on the submission timestamp.

### Topics for public release

Optionally, if you want to release the topics, export the consent-filtered and anonymized release version:

```shell
teaching-ir convert-topics-csv-to-xml --release /path/to/topics.csv topics-release.xml
```

To also export a list of all students who wanted to be listed as coauthors of the released topics file, run:

```shell
teaching-ir convert-topics-csv-to-xml --release --coauthors-path coauthors.txt /path/to/topics.csv topics-release.xml
```

This will then also export a list with newline-separated names of coauthors to include.

## Run the pooling via ChatNoir and TIREx

If you want to look at some recent iterations of this pattern, please have a look here: [https://github.com/OpenWebSearch/wows-code/tree/main/ecir26/collection#setting-up-doccano-step-by-step](https://github.com/OpenWebSearch/wows-code/tree/main/ecir26/collection#setting-up-doccano-step-by-step).

Create top-k pools of documents retrieved by TIREx baselines (using the previously exported `topics.xml` file).

Please create a `config.json` file with the following details:

```
{
    "topics": "THE_NAME_OF_THE_TOPICS_FILE",
    "runs": "runs",
    "team-mapping": "topic-mapping.jsonl",
    "chatnoir-index": "THE_CHATNOIR_INDEX"
}
```

Please create a file `topic-mapping.jsonl` with lines like:

```
{"account": "ir-25-fsu-51", "topics": ["51"]}
```

Now, you can run the pooling


```shell
teaching-ir pool-documents --pooling-depth XX directory
```

## Prepare relevance judgments on Doccano

We also include tools that ease uploading pooled documents and downloading relevance judgments to/from the Doccano annotation platform.

Simply prepare the relevance judgments in Doccano like so:

```shell
teaching-ir prepare-relevance-judgments --doccano-url https://doccano.web.webis.de/ --doccano-username <USERNAME> --doccano-password <PASSWORD> <PREFIX> doccano-judgment-pool.jsonl
```

This will use the pooled documents from the `doccano-judgment-pool.jsonl` file to create for each account of the `topic-mapping.jsonl` file an account to log in to Doccano together with the batch of query-document pairs to judge.

The student teams can now work on their relevance judgments.

## Export relevance judgments

Export the relevance judgments as [qrels](https://trec.nist.gov/data/qrels_eng/) from Doccano like so:

```shell
teaching-ir export-relevance-judgments --doccano-url https://doccano.web.webis.de/ --doccano-username <USERNAME> --doccano-password <PASSWORD> <PREFIX> topics.xml pooling/doccano-judgment-pool.jsonl qrels.txt
```

## Clean up

Once the semester is over and when you have exported all data, clean up the projects and users on Doccano like so:

```shell
teaching-ir clean-up <PREFIX>
```
