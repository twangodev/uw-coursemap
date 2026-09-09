import { expect, it } from "vitest";
import { mkdtemp, mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  finalizeSitemaps,
  pageFingerprint,
  sitemapPolicy,
} from "../sitemap-metadata.mjs";

it("ignores build scripts and footer dates but tracks main content and structured data", () => {
  const page = (content: string, script: string, year: string) =>
    `<title>Course</title><main>${content}<script>${script}</script></main><footer>${year}</footer>`;
  expect(pageFingerprint(page("Java", "a.js", "2026"))).toBe(
    pageFingerprint(page("Java", "b.js", "2027")),
  );
  expect(pageFingerprint(page("Java", "", "2026"))).not.toBe(
    pageFingerprint(page("Python", "", "2026")),
  );
  expect(
    pageFingerprint(
      page("Java", "", "2026") +
        '<script type="application/ld+json">{"a":1}</script>',
    ),
  ).not.toBe(
    pageFingerprint(
      page("Java", "", "2026") +
        '<script type="application/ld+json">{"a":2}</script>',
    ),
  );
});
it("preserves lastmod across unchanged builds and changes it only for changed pages", async () => {
  const root = await mkdtemp(join(tmpdir(), "uw-sitemap-"));
  try {
    await mkdir(join(root, "sitemaps"));
    await writeFile(join(root, "index.html"), "<main>Home</main>");
    await writeFile(join(root, "course.html"), "<main>Java</main>");
    await writeFile(
      join(root, "sitemap.xml"),
      "<sitemapindex><sitemap><loc>https://uwcourses.com/sitemaps/pages-1.xml</loc></sitemap></sitemapindex>",
    );
    await writeFile(
      join(root, "sitemaps/pages-1.xml"),
      "<urlset><url><loc>https://uwcourses.com/</loc></url><url><loc>https://uwcourses.com/course</loc></url></urlset>",
    );
    const run = (now: string) =>
      finalizeSitemaps({
        pages: root,
        output: root,
        history: join(root, "history.json"),
        now,
      });
    await run("2026-09-09T00:00:00.000Z");
    const original = await readFile(join(root, "sitemaps/pages-1.xml"), "utf8");
    await run("2026-09-10T00:00:00.000Z");
    expect(await readFile(join(root, "sitemaps/pages-1.xml"), "utf8")).toBe(
      original,
    );
    await writeFile(join(root, "course.html"), "<main>Python</main>");
    await run("2026-09-11T00:00:00.000Z");
    const changed = await readFile(join(root, "sitemaps/pages-1.xml"), "utf8");
    expect(changed).toContain(
      "<loc>https://uwcourses.com/</loc><lastmod>2026-09-09T00:00:00.000Z",
    );
    expect(changed).toContain(
      "<loc>https://uwcourses.com/course</loc><lastmod>2026-09-11T00:00:00.000Z",
    );
    expect(changed).toContain("<priority>1.0</priority>");
    expect(changed).toContain("<changefreq>weekly</changefreq>");
    expect(await readFile(join(root, "sitemap.xml"), "utf8")).toContain(
      "<lastmod>2026-09-11T00:00:00.000Z</lastmod>",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
it("assigns bounded priorities to the page families", () => {
  for (const path of [
    "/",
    "/departments",
    "/courses/COMPSCI_300",
    "/departments/COMPSCI",
    "/instructors/HOBBES_LEGAULT",
    "/explorer",
  ]) {
    expect(Number(sitemapPolicy(path).priority)).toBeGreaterThanOrEqual(0);
    expect(Number(sitemapPolicy(path).priority)).toBeLessThanOrEqual(1);
  }
});
