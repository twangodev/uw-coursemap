# Quickstart

Install Bun and uv, then run:

```sh
bun install --frozen-lockfile
uv run --locked uwcourses-site import --limit 8
bun run dev
```

The development subset includes CS 300, CS 400 and CS/ECE 759. Omit `--limit` for the full dataset. No external search service or local inference server is needed to develop the website.

```sh
bun run check
bun run test
bun run docs:dev
```

See [architecture](./architecture.md) for the nightly HF-to-Cloudflare publication flow. Scraping and enrichment remain separate local pipeline commands.
