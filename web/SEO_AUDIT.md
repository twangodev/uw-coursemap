# SEO checks

Pages render complete HTML on Cloudflare Workers, including canonical URLs, descriptions, Open Graph metadata, JSON-LD and breadcrumbs. Public document responses are cached per deployment and dataset projection. HTML exposes alternate Markdown/JSON URLs and the OpenAPI description.

Course and instructor URLs preserve the existing readable identifiers. Aliases redirect; missing records return 404. Clean discovery pages are indexable; filtered results, empty rankings, alternate representations and interaction API responses are noindex. Department catalogs link every course without requiring JavaScript.

Sitemaps are built from the pinned dataset, split at 5,000 URLs, and include the source observation timestamp as `lastmod`, priority and change-frequency hints. Personalized 1200×630 social cards are generated from metadata, independently of SSR. The page build no longer fingerprints prerendered HTML.

```sh
bun run check
bun run test
bun run build
bun run seo:check
bun x playwright test web/tests/browser/seo.spec.ts web/tests/browser/documents.spec.ts
```

The static audit verifies sitemap dates, uniqueness, representation exclusions and social images. Browser tests verify server-rendered metadata, canonical navigation, redirects, crawl policy, images and the public API contracts. Run them with `TEST_PREVIEW=1` against a built Worker with local D1 to check production rendering.

After deployment, verify Google Search Console, rich results and field Core Web Vitals. Local tests do not establish indexing or production latency.
