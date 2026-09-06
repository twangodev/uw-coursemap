# Local pipeline

Run from the project root with Python 3.12 and `uv sync --locked`.
The existing `uv run python generation/main.py --step all` workflow remains available during migration.

```sh
export COURSEMAP_WORKSPACE=/path/to/persistent/coursemap
export MADGRADES_API_KEY=...
uv run coursemap run --semester 1272
uv run coursemap status RUN_ID
uv run coursemap resume RUN_ID
uv run coursemap validate RUN_ID
uv run coursemap export RUN_ID
export HF_TOKEN=...
uv run coursemap publish RUN_ID --repo OWNER/DATASET
```

Use the UW enrollment API's four-digit term code. The command prints its run ID
before scraping; source logs are in `runs/RUN_ID/`. The browser-style user agent is fixed for each run and reused on resume.
New runs refresh all HTTP
sources and fetch enrollment for the selected semester. Historical grades remain
included. Embedding models run locally on CUDA when available, otherwise CPU;
model revisions are pinned at run creation. Allow at least 10 GiB free, plus room
for growing history, models, and generated meeting exports.

`resume` skips completed sources, replays saved successful responses for an
interrupted source, and retries failed requests. Code changes require a new run.
To test changed parsers against saved responses:

```sh
uv run coursemap replay OLD_RUN_ID --source catalog
uv run coursemap resume NEW_RUN_ID
```

Replay creates a new run without changing the original. Sources up to the selected
source run offline; missing saved responses cause failure. Resume then completes
the remaining stages, reusing archived responses where available. Only one
mutating CLI command can use a workspace at a time.

## Storage

`pipeline.sqlite` contains versioned observations, SQL views for courses, subjects,
terms, instructors, offerings and grades, and private run/checkpoint state.
`current_*` views select the latest completed run. Raw responses are compressed,
content-addressed local files; request headers are not archived. Keep this
workspace private: source bodies and Scrapy request queues can contain source
authentication details. None of these execution files are exported.

`releases/RUN_ID/` contains a public SQLite database with relational tables and
foreign keys, matching typed Parquet tables, a manifest with file hashes, and
website JSON/GeoJSON compatibility exports. Nested prerequisites, grade details,
and source-specific fields remain JSON columns. SQLite `current_*` views select
the release; history is retained by `run_id`. The generated dataset card describes
its tables and source provenance.

Required sources must complete. Missing subjects, absent target terms, empty
required datasets, unexplained count losses above 10%, and excessive unmatched
enrollment records block a release. Validation also requires reconciled instructors
and target-semester meetings. Failures never advance the local current view.

## Publication

HF publication is explicit and independent of scraping. Uploads use batches of at
most 100 files on `runs/RUN_ID`, with local checkpoints. Retrying `publish` resumes
an interrupted upload. A completed upload gets a `release-RUN_ID` tag, then a single
commit updates `latest.json` on the dataset's main branch. Concurrent changes to
main block promotion rather than overwriting another release.

Consumers read `latest.json`, then use its immutable `revision` for **all** files.
The dataset tables and Dataset Viewer configuration are on that revision/tag;
main holds the publication pointer. To roll back, consumers can pin a previous
release tag. Website logical paths map to
`web/<sha256(logical_path)[:2]>/<logical_path>` to avoid oversized HF directories.

This branch does not activate a Cloudflare deployment or change the production
GitHub Actions scrape.

## Tests

```sh
uv run python -m unittest discover -s generation/tests -v
uv run ruff check generation
uv run ruff format --check generation
```
