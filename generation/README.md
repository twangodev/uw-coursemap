# Local pipeline

Run from the project root with Python 3.12 and `uv sync --locked`.
The legacy `generation/main.py` entrypoint remains during migration; its model stages
also require local inference servers and explicit `COURSEMAP_EMBEDDING_REVISION` /
`COURSEMAP_KEYWORD_REVISION` values.

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
included. All model inference runs through local vLLM servers; model revisions are pinned
at run creation. The scraper never loads model weights itself. Allow at least 10 GiB free, plus room
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

This branch does not activate a Cloudflare deployment. Before merging, retire or
reconfigure the legacy GitHub Actions scrape: hosted runners cannot reach the
workstation inference servers.

## Local inference

The independent `inference/` uv project locks vLLM and its GPU runtime. Once a
scrape prints its run ID, start these in separate terminals before derivation:

```sh
uv run python scripts/serve_inference.py --workspace "$COURSEMAP_WORKSPACE" --run RUN_ID --kind embedding
uv run python scripts/serve_inference.py --workspace "$COURSEMAP_WORKSPACE" --run RUN_ID --kind keyword
```

The servers bind to loopback ports 8001 and 8002 and use the run's exact model
revisions, mean pooling, and normalized embeddings. Set
`COURSEMAP_EMBEDDING_BASE_URL` / `COURSEMAP_KEYWORD_BASE_URL` to override their
`http://127.0.0.1:PORT/v1` URLs; optional authentication uses
`COURSEMAP_INFERENCE_API_KEY`. Model names served by alternative endpoints must
be `HF_MODEL_ID@COMMIT_SHA`. The client validates identity, response ordering,
vector dimensions, and finite values, and retries transient failures. Cached
vectors are separated from the previous direct-inference backend. Generative
LLM enrichment is not implemented yet; it should use the same server boundary.

## One-time legacy backfill

Read the initialized data submodule directly, without checking out historical trees:

```sh
uv run python scripts/backfill_legacy.py --repository /path/to/uw-coursemap/data --workspace "$COURSEMAP_WORKSPACE"
uv run python scripts/backfill_legacy.py --repository /path/to/uw-coursemap/data --workspace "$COURSEMAP_WORKSPACE" --all
```

The first command imports HEAD; `--all` imports all reachable commits. Each commit
is atomic and safe to rerun. Snapshots retain `update.json` timestamps and Git
commit provenance. Current views select the newest observation, so backfilling
older data cannot replace a newer scrape. Historical grade totals are separate
snapshots: do not sum them across runs.

The importer preserves course and instructor JSON, including legacy enrichment,
and per-course meetings when available. Raw responses and model provenance are
unavailable. The scrape semester is inferred from enrollment terms and marked as
inferred. Legacy snapshots join the next fresh release's SQLite and Parquet
history; they cannot produce standalone website releases. No LLMs run during
backfill. Generated graphs and redundant website exports remain recoverable from
Git rather than being imported into the database.

## Tests

```sh
uv run python -m unittest discover -s generation/tests -v
uv run ruff check generation
uv run ruff format --check generation
```
