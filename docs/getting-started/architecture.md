# Architecture

The local Python pipeline scrapes source data and runs LLM enrichment, then publishes historical Parquet tables to [Hugging Face](https://huggingface.co/datasets/twangodev/uw-coursemap).

A nightly GitHub Actions workflow pins that dataset revision. The `uwcourses_site` Python package validates and imports it into website-specific SQLite/D1 tables and bounded static evidence files. SvelteKit prerenders courses, departments and current instructors. Native Wrangler commands stage the inactive D1 database and deploy the matching Worker and assets.

Cloudflare Workers Static Assets serves pages, histories and model traces. Same-origin `/api` endpoints provide D1 full-text search and structured filtering. Historical instructor pages render on demand. No scraping or inference runs in the request path.

See the repository's [website guide](https://github.com/twangodev/uw-coursemap/blob/main/web/README.md) for setup, validation and deployment.
