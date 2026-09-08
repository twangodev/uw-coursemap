# Generation

The local Python pipeline lives in `generation/uw_coursemap` and runs manually each
semester. Use Python 3.12 and run commands from the project root:

```sh
uv sync --locked
export COURSEMAP_WORKSPACE=/path/to/persistent/coursemap
uv run coursemap scrape --semester 1272
uv run coursemap status RUN_ID
```

Scrapy collects the catalog, enrollment, grades, faculty, and Rate My Professors
records into a validated, immutable snapshot. Successful responses are archived
for recovery and offline replay.

Enrichment uses a separately managed vLLM or compatible server. It produces
course metadata, prerequisite trees, cited student summaries, and saved model
traces. Model identities and task versions are recorded with the results.

`release` combines
source history and selected enrichment jobs into relational Parquet tables;
`publish --parquet-only` uploads the release to Hugging Face. Raw history is retained
so consumers can derive their own statistics. Search indexes and website responses
belong to the consuming Worker; no static website files are generated.

The historical importer remains available for recovering old snapshots from Git.
Existing snapshots can be read and released without the former data submodule.

See the [pipeline command reference](https://github.com/twangodev/uw-coursemap/blob/main/generation/README.md)
for inference setup, repair, historical import, and publication commands.
