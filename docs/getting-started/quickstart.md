# Quickstart

## Frontend

Clone the repository, configure the public API endpoints, and install dependencies:

```sh
git clone https://github.com/twangodev/uw-coursemap.git
cd uw-coursemap
cp .env.example .env
npm ci
npm run dev
```

The frontend currently uses `PUBLIC_API_URL` for course data and
`PUBLIC_SEARCH_API_URL` for search and random-course requests. These services are
external to this checkout. The replacement Parquet-backed Worker is planned.

To preview the documentation:

```sh
npm run docs:dev
```

## Local data pipeline

Use Python 3.12 and run from the project root:

```sh
uv sync --locked
uv run coursemap --help
```

Set `MADGRADES_API_KEY` and choose a persistent `COURSEMAP_WORKSPACE`. See the
[generation guide](../codebase/generation.md) for scraping, LLM enrichment, and
Hugging Face publication. The dataset is available on
[Hugging Face](https://huggingface.co/datasets/twangodev/uw-coursemap).

## Frontend container

The root Compose file runs only the frontend:

```sh
docker compose up --build web
```

The Flask/Elasticsearch service has been retired. There is no local search server
to start; configure an available endpoint until the Worker migration is complete.
