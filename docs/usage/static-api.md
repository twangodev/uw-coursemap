# Data access

The complete dataset is published as Parquet on [Hugging Face](https://huggingface.co/datasets/twangodev/uw-coursemap). Pin a dataset commit for reproducible analysis. The website builds its own serving database from that revision.

The website exposes these same-origin endpoints:

| Endpoint                         | Purpose                                       |
| -------------------------------- | --------------------------------------------- |
| `/api/status`                    | Active dataset revision and scan metadata     |
| `/api/search`                    | Course or instructor search                   |
| `/api/courses/{uid}/grades`      | Paginated course or instructor-section grades |
| `/api/instructors/{uid}/history` | Paginated teaching history                    |

Search accepts `q`, `kind=course|instructor`, `subject`, `instructor`, `term`, `credits_min`, `credits_max`, `gpa_min`, `sort=gpa`, and `page`. Course filters apply to course results. Search pages contain up to 30 results; grades and teaching history use pages of 100.

Pass `revision` from `/api/status` to detect a dataset change: a mismatch returns HTTP 409. Course pages link to static JSON downloads for the source history, reviews, and model traces.
