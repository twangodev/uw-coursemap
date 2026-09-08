# Frontend

The SvelteKit application is under `src/`. Shared components implement course lists, cited summaries, LayerChart grade charts, Svelte Flow prerequisite trees and lazy evidence inspection.

`src/lib/server/data.ts` owns parameterized D1 queries, alias-aware FTS5 search, grade filtering and revision checks. Development and prerendering use the same SQL against the imported local SQLite database.

`web/uwcourses_site` is the uv-installed Parquet importer and asset-budget checker. It owns disposable serving projections, independently of the scraper's canonical HF publication.

The nightly website workflow builds with Bun on GitHub Actions and publishes using Wrangler. See `web/README.md` in the repository for setup and rollback details.
