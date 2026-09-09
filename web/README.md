# Website

SvelteKit SSR on Cloudflare Workers, with cached responses, static assets, and Drizzle + D1. HF is the source of truth.

```sh
bun install --frozen-lockfile
uv run --locked uwcourses-site import --limit 8
bun run dev
```

Omit `--limit` for the complete dataset. `--source /path/to/release` reads a local release; `--revision HF_COMMIT` pins a remote release. The importer is the `uwcourses_site` Python package, installed by uv. Generated `.site/` and `static/data/` are disposable and ignored by Git.

```sh
bun run check
bun run test
uv run --locked python -m unittest discover -s web/tests -p 'test_*.py'
bun run build
bun run seo:check
uv run --locked uwcourses-site assets-check
bun x playwright test
```

Production preview runs the built Cloudflare Worker with Wrangler and uses local D1, not `.site/site.sqlite`. After importing a new dataset, stop the preview and refresh its database before restarting:

```sh
set -e
for part in .site/sql/*.sql; do
  bun x wrangler d1 execute DB_BLUE --local --file="$part"
done
bun run preview --ip 0.0.0.0 --port 4173
```

`TEST_PREVIEW=1 bun x playwright test` runs browser checks against the production preview. Set `TEST_PORT` to use a different port.

## Cloudflare setup

Create D1 databases `uw-coursemap-blue` and `uw-coursemap-green`, then put their IDs in `wrangler.jsonc`. Set GitHub secrets `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` with Workers Scripts and D1 edit permissions. `HF_TOKEN` is optional for the public dataset.

Run the nightly workflow manually with **First deployment** enabled once to create the Worker. Validate its workers.dev preview, then attach `uwcourses.com` in Cloudflare. Subsequent runs leave that option disabled.

GitHub Actions runs at 03:17 America/Los_Angeles and also supports **Run workflow**. It pins HF, imports locally, builds and tests, then uses native Wrangler commands to import the inactive D1 database and deploy matching code/assets with the new database selection. Only this workflow should modify these production databases. When the HF revision and importer are unchanged, the active database is reused while the site still rebuilds and redeploys. No separate deployment scripts or Cloudflare cron are needed.

Failures before deployment preserve the active database/site. The previous deployment can be restored using Cloudflare's Worker rollback while its database remains intact; the next import into that slot replaces it. Production jobs are serialized. GitHub stores release metadata for each run. GitHub may disable schedules after 60 days without repository activity; re-enable the workflow from Actions if needed.

D1 SQL is emitted as ordered 16 MiB files, with each statement below 100 KB. The workflow imports them sequentially and checks a completion marker and dataset identity before deployment.

History and traces are paged static JSON. Unusually large trace records use ordered text fragments that concatenate to the original JSON. Assets are checked against 90,000 files and 20 MiB per file. Search and filtered grades use `/api`; outdated page requests return 409 and ask the student to reload.

Grades use course aggregates or instructor sections, never both. Identical cross-list distributions are deduplicated; conflicting course/term distributions are preserved for inspection and excluded from calculated GPA. Co-teachers share a section's distribution. Catalog timestamps represent observations, not validity intervals. Instructor identities remain separate even when names match.

Social cards use `web/social-card.html` and are generated automatically from dataset metadata by the Cloudflare adapter, without rendering the website pages. Chromium is required (`bun x playwright install chromium`). The renderer caches unchanged titles, fonts and artwork under `.site/social-cache`; production serves static PNGs, while Vite generates preview cards on demand.

Sitemaps remain build-time assets. Their `lastmod` is the dataset observation timestamp, not the deployment timestamp; priorities and change frequencies are included.

## Public representations

Append `.json` or `.md` to a page URL (`/courses/COMPSCI_300.json`, `/search.md?q=java`); the homepage uses `/index.json` and `/index.md`. HTML advertises both via HTTP `Link` and `<link rel="alternate">`. These are public, read-only APIs with CORS enabled; alternate formats are noindex.

`/openapi.json` serves OpenAPI 3.1, generated from the same Zod schemas used to validate document responses. TypeScript consumers can import inferred types from `src/lib/api/schemas.ts` or generate a client from the spec. Core entities have named fields; additional source fields use the recursive `JsonValue` schema. The existing `/api` interaction endpoints are also documented and validated.

JSON has `schema_version`, `url`, `title`, `dataset`, and `data`. The dataset includes its pinned HF revision and projection identity. `data` is the same payload the page loader returns; nested LLM evidence and model provenance are retained. Large history/trace files remain linked from that payload rather than duplicated. Markdown renders the same records, with tables and JSON blocks for nested data. Neither format requires browser JavaScript.

Public GET documents are cached for 24 hours in Cloudflare's Cache API. Keys include the deployment, data projection, database slot, URL, and query. Browser responses revalidate with ETags. Cache hits still invoke the Worker; the cache is local to each data center. Authenticated/cookie requests, navigation transport, errors, and existing `/api` endpoints bypass this document cache. Preview caching requires `SITE_COMMIT` and `DATA_PROJECTION`; without them requests render directly.

Drizzle owns website reads; the Python importer owns the read-model schema and ordered SQL import. Complex FTS and grade aggregations use bound SQL through Drizzle on D1. Development reads the imported local SQLite database.
