# Course search SEO audit

Audited on September 9, 2026, against `feat/hf-workers-site` at `35806f9`. The public COMPSCI 300 page still serves the older frontend, so these findings describe the replacement branch, not a deployed change or a ranking measurement.

## Findings and changes

| Area | Finding | Result |
| --- | --- | --- |
| Crawling and indexing | Course pages already prerender their content; course aliases already redirect permanently. | Preserved readable URLs and cross-list identity. Added regression checks for HTML without JavaScript, aliases, and real 404s. |
| Sitemap | `robots.txt` advertised `/sitemap.xml`, but the branch had no sitemap implementation. | Added a prerendered sitemap index and files of at most 5,000 URLs. Includes every course, department catalogs, department landing pages, course collections, and the publication's selected instructor pages. |
| Canonicals | Course, department, and instructor canonicals were relative; other page families lacked them. | One absolute production canonical per page, with consistent percent encoding for department codes containing `&`. Filter, term, tracking, and fragment variants consolidate onto the clean path. |
| Duplicate routes | `/subjects`, `/stats`, and `/stats/{subject}` duplicated department pages. | Permanent redirects to `/departments` and `/departments/{subject}`, preserving query parameters. Internal homepage links now use the destination directly. |
| Course discovery | Department pages initially exposed only 30 filtered results. Search and pagination were the main route to the rest of the catalog. | Added linked, prerendered `/departments/{subject}/catalog` pages containing every recorded course, including courses not offered in the selected term. Course breadcrumbs link back to departments. |
| Thin ranking pages | 54 department ranking pages have no eligible courses in the current snapshot. | Empty rankings are noindex and omitted from the sitemap; populated rankings remain indexable. |
| Source links without JavaScript | Course-card citations linked to a nonexistent local `#evidence` section on department and instructor lists. | Citation fallbacks now link to the course’s real evidence section; grade links in the popup also target that course. |
| Titles and snippets | Course titles omitted UW–Madison; some descriptions used unbounded AI summaries. Homepage metadata emphasized a slogan. | Course identifiers, readable titles, UW–Madison, and course-search intent now appear in metadata. Course snippets use catalog information and are bounded. Each page family gets appropriate metadata. |
| Structured data | No JSON-LD. | Added `Course`, `BreadcrumbList`, `WebSite`, and course-list `ItemList` markup. Course descriptions and prerequisites come from catalog fields; the university is the course provider. Lists describe rendered links only. Imported text is escaped against script termination. |
| Missing source facts | 50 courses lack catalog descriptions, and five selected instructor records lack names. | Courses retain their useful pages and breadcrumbs but omit incomplete Course markup. Unnamed instructor records are noindex and excluded from the sitemap. No missing descriptions or identities are invented. |
| Ratings and content integrity | The site contains adjusted instructor ratings, AI summaries, and historical grade projections. | These are not represented as course review stars, official offerings, or guaranteed outcomes in structured data. Existing source links, provenance, and non-affiliation text remain visible. |
| Search and auxiliary data | Search was already noindex; errors and downloadable data lacked explicit policy. | Preserved search noindex, added error-page noindex and titles, and added `X-Robots-Tag: noindex` for API responses and static evidence JSON. Rendering resources remain crawlable. |
| Social previews | Metadata varied by page family. | Centralized Open Graph and Twitter title, description, URL, locale, and site name alongside search metadata. |
| Mobile and performance | Responsive layouts, server rendering, locally hosted fonts with `font-display: swap`, and deferred interactive maps already exist. Course pages serialize substantial historical data. | Preserved these mechanisms. The built audit reports representative HTML and gzip sizes; field Core Web Vitals still require measurement after deployment. |
| Regression prevention | No catalog-wide SEO check. | Added unit and browser checks plus `bun run seo:check` after build in both website CI workflows. It checks sitemap targets, canonical/title/description/robots tags, parseable JSON-LD, headings, course identity, and full catalog link coverage. |

The sitemap intentionally omits `lastmod`: dataset scan time is not evidence that each page's substantive content changed. It also omits arbitrary priority and change-frequency values. The instructor sitemap follows the publication's selected pages rather than promoting all historical identities. Ten pairs of named instructor records share a name and title; their distinct identities and canonical URLs are preserved rather than merging people based on name alone. Interactive subject maps remain accessible from departments; their canvas content is not used as a substitute for crawlable course catalogs.

## Validation

Run after importing the dataset:

```sh
bun run check
bun run test
bun run build
bun run seo:check
bun x playwright test web/tests/browser/seo.spec.ts web/tests/browser/course-urls.spec.ts web/tests/browser/legacy-urls.spec.ts
```

The audited dataset contains 8,951 courses, 187 departments, and 5,754 selected instructor pages (5,749 with names eligible for the sitemap). Validation passed: 73 unit tests, eight browser tests, Svelte checking with no errors or warnings, the full production build, and the strict audit of 15,399 sitemap URLs across five files. All 8,951 courses have catalog links; 8,901 have complete Course markup, and 54 empty ranking pages are noindex. The final build reports no missing-fragment warnings.

The Cloudflare package contains 65,673 assets; the largest is 1,684,140 bytes. Local Cloudflare preview checks confirmed XML responses, exact encoded canonicals, query-preserving redirects, the static evidence noindex header, and the robots sitemap reference. Production D1 and Google indexing were not tested or changed.

Representative generated HTML sizes (gzip, excluding JavaScript and other assets): homepage 5,921 bytes; COMPSCI 300 36,699 bytes; Computer Sciences catalog 42,931 bytes. These are transfer-size observations, not Core Web Vitals scores. The audit command reports fresh counts and sizes for future datasets.

## After deployment

1. Verify the `uwcourses.com` property in Google Search Console and submit `https://uwcourses.com/sitemap.xml`. Confirm production returns the new XML and absolute canonicals.
2. Inspect a normal course, a cross-listed course, a department catalog, and an instructor URL using URL Inspection. Use Google's Rich Results Test for Course and breadcrumb markup. Local JSON validation does not establish Google's rich-result eligibility.
3. Check Page Indexing for unexpected exclusions, duplicate canonical selection, soft 404s, and sitemap processing errors. Keep old course aliases redirecting to their established canonical URLs.
4. Measure mobile Core Web Vitals and inspect representative course payloads. If LCP or INP is poor, profile historical-data hydration and chart execution before changing content delivery; keep the catalog description and prerequisites in initial HTML.
5. Track impressions, clicks, position, and CTR for course-code searches such as “UW Madison CS 300,” “COMPSCI 300 prerequisites,” and “Math 221 UW Madison grades,” comparing equivalent periods and accounting for semester seasonality. Search Console access, backlinks, and field metrics were not available in this audit; ranking gains have not been measured.

These changes improve discoverability and clarify page meaning. They do not guarantee indexing, rich results, or placement above the official university catalog. Earned links from useful student and departmental resources, reliable data, and demonstrated student usefulness remain ongoing work.

## References

- [Google: JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Google: canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google: sitemap construction and submission](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google: Course list structured data](https://developers.google.com/search/docs/appearance/structured-data/course)
- [Google: breadcrumb structured data](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)

## Incremental follow-up: hydration responses

Hydration JSON now receives `X-Robots-Tag: noindex` both from static assets and dynamic responses. Instructor data requests bypass the HTML cache using SvelteKit's `isDataRequest` flag; URL suffix checks are insufficient because SvelteKit strips the suffix before invoking hooks. Four regression tests pass. A local Cloudflare assets fixture confirmed the header on root, course, and nested catalog hydration JSON, while its HTML control remained indexable. The generated-output audit now checks both hydration header rules.
