# Local pipeline

Run from the project root with Python 3.12 and `uv sync --locked`. Scraping,
processing, and publication are independent commands with persistent checkpoints.

```sh
export COURSEMAP_WORKSPACE=/path/to/persistent/coursemap
export MADGRADES_API_KEY=...
uv run coursemap scrape --semester 1272
uv run coursemap status RUN_ID
uv run coursemap resume RUN_ID
uv run coursemap release RUN_ID
export HF_TOKEN=...
uv run coursemap publish RELEASE_ID --repo OWNER/DATASET
```

Use UW's four-digit enrollment term code. Scraping collects the catalog, Madgrades
history, and enrollment for that semester, then validates and freezes a source
snapshot. It does **not** require inference servers or download model weights.
Faculty-directory and ratings scraping is opt-in with `--include-instructors`;
when requested, those sources must also finish. Instructors reported by enrollment
and grades are retained without that option.

The command prints its ID before starting. Logs live in `runs/RUN_ID/`. A fixed
browser-style user agent is reused on resume. Successful sources are skipped;
interrupted sources reuse archived successful responses and retry failures.
Independent sources continue when another source fails. Defaults allow 32 requests
in flight, 16 per domain, with adaptive throttling targeting 8 per domain and a
0.1-second download delay. Override with `--concurrency`, `--per-domain`,
`--target-concurrency`, and `--download-delay`; limits are recorded in the snapshot. Failed runs never advance
`current_*` views. Keep at least 10 GiB free, plus room for history and exports.

Changed parser code requires a new snapshot. To reuse archived responses:

```sh
uv run coursemap replay OLD_RUN_ID --source catalog
uv run coursemap resume NEW_RUN_ID
```

Replay runs sources up through the selected source offline; missing archived
responses fail explicitly. Resume collects the remaining sources normally. Keep
an active scraper on its original checkout and uv environment until it finishes.

## Optional processing

Model profiles live in `inference/models.toml`. Pin the selected profiles once;
both clients and server launchers use the resulting JSON file:

```sh
uv run coursemap models-lock --models-config inference/models.toml \
  --profile embedding --profile keyword --profile enrichment \
  --output "$COURSEMAP_WORKSPACE/models.lock.json"
```

In separate terminals, start only the servers needed for the chosen job:

```sh
uv run python scripts/serve_inference.py --workspace "$COURSEMAP_WORKSPACE" \
  --models-config "$COURSEMAP_WORKSPACE/models.lock.json" --profile embedding
uv run python scripts/serve_inference.py --workspace "$COURSEMAP_WORKSPACE" \
  --models-config "$COURSEMAP_WORKSPACE/models.lock.json" --profile keyword
uv run python scripts/serve_inference.py --workspace "$COURSEMAP_WORKSPACE" \
  --models-config "$COURSEMAP_WORKSPACE/models.lock.json" --profile enrichment
```

The separate `inference/` uv project locks vLLM and its GPU dependencies. Servers
bind to loopback; `--dry-run` prints a launch command without downloading weights.
Profiles control model/revision, token limits, dimensions, document prefix,
concurrency, pooling, and server arguments. Alternative vLLM/SGLang servers can
use the same HTTP boundary; serve the identity `HF_MODEL_ID@COMMIT_SHA` and record
the actual engine/version in the profile. Optional authentication uses
`COURSEMAP_INFERENCE_API_KEY`. No client loads model weights directly.

The default generation candidate is Qwen3.6-35B-A3B-FP8. Select
`enrichment-nvfp4` for NVIDIA's Qwen3.6-35B-A3B-NVFP4, or `enrichment-bf16` as a
reference. Lock that profile and use the same name in the server and enrichment
commands. These are configurable candidates, not task-quality benchmark results.
Generation concurrency defaults to 16 for FP8, 32 for NVFP4, and 8 for BF16;
embedding profiles permit 16 concurrent batches of up to 32 texts per request.
These are initial throughput settings; lower concurrency if memory pressure or
latency warrants it. Lock profiles again to adopt changed defaults.
Run one generation profile at a time; BF16's larger memory allocation requires
stopping the embedding servers first.

Build existing similarity, keywords, prerequisite display graphs, and website
compatibility files with the embedding and keyword servers:

```sh
uv run coursemap derive RUN_ID --models-config "$COURSEMAP_WORKSPACE/models.lock.json"
uv run coursemap derive-resume BUILD_ID
```

Builds copy one immutable snapshot into `builds/BUILD_ID/`, checkpoint each stage,
and leave source data unchanged. Embeddings use bounded batches and disk caching.
Cache identities include model and processing settings. Original prerequisite
text/structure remains in source tables; optimized graph choices are derivatives.

For generative enrichment, start with a stable sample of 100 courses:

```sh
uv run coursemap enrich RUN_ID --models-config "$COURSEMAP_WORKSPACE/models.lock.json" \
  --task inference/tasks/course_profiles.json --limit 100
uv run coursemap job-status ENRICHMENT_ID
uv run coursemap enrich-resume ENRICHMENT_ID
```

`--prepare-only` creates a job without contacting inference; `--limit 0` selects
all courses. The task file defines source inputs, prompt, JSON Schema, and task
version. The initial task produces summaries, topics, skills, and search phrases;
topic/skill evidence must quote the description. It does not estimate workload,
grades, or instructor quality. Schema and exact-quote checks reject malformed
outputs, but human review is still needed to assess semantic quality.

`processing.sqlite` records per-course inputs, outputs, usage, failures, and
immutable task/model provenance. A single writer commits bounded concurrent HTTP
results. Resume retries unfinished courses; unchanged inputs reuse validated
outputs across snapshots. Prompt, schema, model, and generation settings change
the cache identity. Completed jobs cannot be silently overwritten.

Explicitly select optional outputs for a release:

```sh
uv run coursemap release RUN_ID --build BUILD_ID --enrichment ENRICHMENT_ID
uv run coursemap publish RELEASE_ID --repo OWNER/DATASET
```

Repeat `--enrichment` to attach multiple completed jobs. Partial or failed jobs
cannot be released; completed samples include their coverage counts. A source-only
release remains available even when an optional model job fails. Scraping,
derivation, enrichment, and publication have separate locks; different processing
jobs can run alongside a scrape. Each build/job permits only one active worker.

## Qwen requirements parsing

Lock the `requirements` profile and launch it using the same model-server command.
It uses Qwen3.6-35B-A3B-NVFP4 with a 16K context and 4K output budget:

```sh
uv run coursemap enrich RUN_ID --models-config "$COURSEMAP_WORKSPACE/qwen-models.lock.json" \
  --profile requirements --task inference/tasks/requirements.json --limit 100
```

The task receives raw requirements text and linked course references, excluding
existing parser output. Results contain an AND/OR/NOT tree, course timing and grade
qualifiers, verbatim non-course conditions, evidence quotes, and review notes.
Structural validation rejects cycles, missing nodes, invented course references,
and quotes absent from the source. Ambiguous rules are marked `needs_review`.
Whitespace-equivalent evidence is restored to its literal source substring before
validation; other quote differences are rejected. Retries receive validation
feedback. The model sees the schema as well as the constrained output grammar.
A separate `Not open to students with credit for ...` sentence must constrain all
eligibility alternatives in a parsed result. Review notes are bounded, and failed
rows retain a short validation reason for diagnosis.
These checks cannot prove semantic equivalence; review the pilot before using the
results for eligibility or replacing existing graphs. Parsed requirements remain
separate enrichment records, with the original wording preserved.

Run the small manually checked regression benchmark before changing the task or
model, then inspect a fresh catalog sample. The benchmark checks Boolean grouping,
exclusions, grades, concurrency, and review status; it is a development suite,
not an estimate of catalog-wide accuracy.

```sh
uv run python scripts/evaluate_requirements.py \
  --models-config "$COURSEMAP_WORKSPACE/qwen-models.lock.json" \
  --output "$COURSEMAP_WORKSPACE/audits/requirements-eval.json"
```

## Storage and Hugging Face

`pipeline.sqlite` stores versioned observations and source checkpoints. Compressed,
content-addressed raw responses remain local. Keep the workspace private: raw
bodies and Scrapy queues may contain authentication details. They are not exported.

`releases/RELEASE_ID/` contains a public relational SQLite database, equivalent
Parquet tables, a dataset card, and a checksummed manifest. Nested source structures
remain JSON columns. History joins by `run_id`; `current_*` views select the chosen
snapshot. Releases record source history, exporter identity, selected build/model
provenance, and enrichment coverage. Website files are included only with `--build`.
Missing required data, reference errors, and unexplained count drops block source
completion. SQLite foreign keys and file hashes are checked before publication.

HF uploads are explicit, batched, resumable, and tagged by immutable revision.
Only a completed upload promotes `latest.json` on the dataset's main branch;
concurrent pointer changes block promotion. Consumers read that pointer and use
its exact `revision` for every file. SQLite/Parquet and Dataset Viewer configuration
live on the release revision. Website paths map to
`web/<sha256(logical_path)[:2]>/<logical_path>` to avoid oversized HF directories.

No Cloudflare deployment is activated here. Before merging, retire or reconfigure
the legacy hosted GitHub Actions scrape; it cannot reach local inference servers.
Older combined runs can still resume with their original checkout and configuration.

Instructor reconciliation indexes parsed names by exact normalized surname, then
uses up to 24 CPU processes in batches of 256. Set `COURSEMAP_NAME_WORKERS` to
change the worker count. A single writer checkpoints results; cache keys include
the candidate roster, and ties use stable candidate ordering.

## One-time backfill

```sh
uv run python scripts/backfill_legacy.py --repository /path/to/uw-coursemap/data \
  --workspace "$COURSEMAP_WORKSPACE" --all
```

Without `--all`, imports HEAD only. Each Git commit imports atomically and is safe
to rerun. Observation timestamps prevent old backfills replacing newer snapshots.
Legacy course/instructor JSON and available meetings are retained; unavailable raw
responses and model provenance are not invented. Historical grade totals are
snapshots: **do not sum them across runs**. Legacy snapshots can be released or
used for generative enrichment, but lack raw inputs for rebuilding website graphs.

## Checks

```sh
uv run python -m unittest discover -s generation/tests -v
uv run ruff check generation scripts/serve_inference.py
uv run ruff format --check generation scripts/serve_inference.py
```
