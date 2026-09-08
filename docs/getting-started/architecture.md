# Architecture

The repository contains a SvelteKit frontend and a local Python data pipeline.

The pipeline manually collects course, enrollment, grade, faculty, and review
records each semester. A separate inference server adds structured metadata,
prerequisite trees, and cited student summaries. Releases preserve source history
and model traces in relational Parquet tables on
[Hugging Face](https://huggingface.co/datasets/twangodev/uw-coursemap).

The frontend currently consumes externally hosted data through `PUBLIC_API_URL`
and search through `PUBLIC_SEARCH_API_URL`. Its existing search interface uses
`POST /search` and `GET /random-courses`.

The Flask/Elasticsearch service and static website export pipeline have been
removed. The planned Cloudflare Worker will ingest Parquet and own API responses
and search indexing. That Worker is not implemented in this checkout yet.

See [frontend](../codebase/frontend.md) and
[generation](../codebase/generation.md) for the maintained code paths.
