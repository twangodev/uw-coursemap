import { query, status } from "$lib/server/data";
import { instructorUrls } from "$lib/server/instructor-urls";
import { absoluteUrl } from "$lib/seo";
import { courseUrl } from "$lib/format";
import { courseCollections } from "$lib/course-collections";
import entries from "../../../.site/import/entries.json";

export const sitemapSize = 5000;
export function escapeXml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
export function sitemapXml(paths: string[], index = false, lastmod?: string) {
  const root = index ? "sitemapindex" : "urlset";
  const item = index ? "sitemap" : "url";
  return `<?xml version="1.0" encoding="UTF-8"?>\n<${root} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map((path) => `<${item}><loc>${escapeXml(absoluteUrl(path))}</loc>${lastmod ? `<lastmod>${escapeXml(lastmod)}</lastmod>` : ""}${index ? "" : `<changefreq>${path === "/" ? "weekly" : "monthly"}</changefreq><priority>${path === "/" ? "1.0" : path.startsWith("/courses/") ? "0.8" : path.startsWith("/instructors/") ? "0.6" : "0.7"}</priority>`}</${item}>`).join("")}</${root}>`;
}
let cached: Promise<Map<string, string[]>> | undefined;
// Prepared alongside serving documents from the same pinned import.
export function sitemapPages() {
  return (cached ??= (async () => {
    const [courses, instructors, named] = await Promise.all([
      query(undefined, "SELECT code FROM courses ORDER BY code"),
      instructorUrls(),
      query(
        undefined,
        "SELECT uid FROM instructors WHERE name IS NOT NULL AND trim(name)!=''",
      ),
    ]);
    const namedInstructors = new Set(named.map((row) => row.uid));
    const { term } = await status();
    // Match the ranking browser: offered this term, with 100 letter grades
    // in its five-year historical window. Empty ranking pages are noindex.
    const ranked = await query(
      undefined,
      `
      WITH eligible AS (
        SELECT uid FROM grade_summaries
        WHERE term<=? AND CAST(term AS INTEGER)>?
        GROUP BY uid HAVING SUM(a+ab+b+bc+c+d+f)>=100
      )
      SELECT DISTINCT s.subject FROM subjects s
      JOIN eligible e ON e.uid=s.uid JOIN offerings o ON o.uid=s.uid
      WHERE o.term=?`,
      [term, Number(term) - 50, term],
    );
    const rankedSubjects = new Set(ranked.map((row) => row.subject));
    const collections = Object.keys(courseCollections);
    const groups = {
      pages: [
        "/",
        "/departments",
        "/stats",
        "/explorer",
        "/search",
        "/instructors/by-rating-count",
        ...(rankedSubjects.size ? collections.map((c) => `/courses/${c}`) : []),
        ...entries.subjects.flatMap((subject) => {
          const path = `/departments/${encodeURIComponent(subject)}`;
          return [
            path,
            `${path}/catalog`,
            ...(rankedSubjects.has(subject)
              ? collections.map((c) => `${path}/${c}`)
              : []),
          ];
        }),
      ],
      courses: courses.map((course) => courseUrl(course.code)),
      // Match the publication's selected instructor pages, not every historical identity.
      instructors: entries.instructors
        .filter((uid) => namedInstructors.has(uid))
        .map((uid) => {
          const path = instructors.get(uid);
          if (!path) throw new Error(`Missing instructor URL: ${uid}`);
          return path;
        }),
    };
    const pages = new Map<string, string[]>();
    for (const [kind, paths] of Object.entries(groups)) {
      if (new Set(paths).size !== paths.length)
        throw new Error(`Duplicate ${kind} sitemap URLs`);
      for (let offset = 0; offset < paths.length; offset += sitemapSize)
        pages.set(
          `${kind}-${offset / sitemapSize + 1}.xml`,
          paths.slice(offset, offset + sitemapSize),
        );
    }
    return pages;
  })());
}
export const xmlHeaders = { "Content-Type": "application/xml; charset=utf-8" };
