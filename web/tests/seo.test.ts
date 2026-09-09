import { describe, expect, it, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: true }));
import { absoluteUrl, courseSchema, jsonLd, pageSeo } from "../../src/lib/seo";
import {
  sitemapPages,
  sitemapXml,
  sitemapSize,
} from "../../src/lib/server/sitemap";
import { query, search } from "../../src/lib/server/data";
import { courseUrl } from "../../src/lib/format";

describe("search metadata", () => {
  const course = {
    course_id: "COMPSCI 300",
    title: "PROGRAMMING II",
    description: "Introduction to object-oriented programming.",
    requirements_text: "COMP SCI 200",
    subjects: ["COMPSCI"],
  };
  it("uses the course identity and catalog facts on the production canonical", () => {
    const seo = pageSeo({ course }, "/courses/cs-300");
    expect(seo.title).toBe("COMPSCI 300: Programming II | UW–Madison");
    expect(seo.description).toContain("UW–Madison");
    expect(seo.description.length).toBeLessThanOrEqual(160);
    expect(seo.canonical).toBe("https://uwcourses.com/courses/COMPSCI_300");
    expect(
      courseSchema({ ...course, llm_summary: "Invented fact" }),
    ).toMatchObject({
      description: course.description,
      coursePrerequisites: "COMP SCI 200",
      provider: { name: "University of Wisconsin–Madison" },
    });
    expect(seo.structuredData["@graph"]).toHaveLength(2);
  });
  it("does not let preview hosts or filters define the canonical", () => {
    expect(
      absoluteUrl(
        "https://preview.example/departments/COMPSCI?term=1262#grades",
      ),
    ).toBe("https://uwcourses.com/departments/COMPSCI");
  });
  it("marks search and errors noindex and gives errors their own title", () => {
    expect(pageSeo({}, "/search").noindex).toBe(true);
    expect(pageSeo({}, "/instructors/by-rating-count").noindex).toBe(true);
    expect(pageSeo({ course }, "/courses/missing", 404)).toMatchObject({
      noindex: true,
      title: "Page not found | UW Courses",
    });
    expect(pageSeo({ course }, "/courses/COMPSCI_300").noindex).toBe(false);
  });
  it("escapes imported text so JSON-LD cannot terminate its script", () => {
    const value = { description: '</script><script>alert("x")</script>\u2028' };
    expect(jsonLd(value)).not.toContain("<");
    expect(JSON.parse(jsonLd(value))).toEqual(value);
  });
  it("lists only courses displayed in a department catalog", () => {
    const seo = pageSeo(
      { subject: "COMPSCI", catalog: [course] },
      "/departments/COMPSCI/catalog",
    );
    expect(seo.title).toContain("Course Catalog");
    expect(seo.structuredData["@graph"]).toContainEqual(
      expect.objectContaining({
        "@type": "ItemList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            url: absoluteUrl(courseUrl(course.course_id)),
          },
        ],
      }),
    );
  });
});

it("publishes every canonical course exactly once in bounded XML sitemaps", async () => {
  const pages = await sitemapPages();
  const urls = [...pages.values()].flat();
  expect(new Set(urls).size).toBe(urls.length);
  expect(
    [...pages.values()].every((paths) => paths.length <= sitemapSize),
  ).toBe(true);
  const courses = await query(undefined, "SELECT code FROM courses");
  expect(
    urls
      .filter(
        (path) =>
          path.startsWith("/courses/") &&
          !["/courses/easiest", "/courses/hardest"].includes(path),
      )
      .sort(),
  ).toEqual(courses.map((c) => courseUrl(c.code)).sort());
  expect(
    urls.some((path) =>
      /[?#]|^\/search|^\/stats|^\/subjects|course_/.test(path),
    ),
  ).toBe(false);
  for (const paths of pages.values())
    expect(Buffer.byteLength(sitemapXml(paths))).toBeLessThan(50 * 1024 * 1024);
  expect(sitemapXml(["/courses/A%26B_100"])).toContain(
    "https://uwcourses.com/courses/A%26B_100",
  );
});

it("omits empty rankings while preserving populated ranking pages", async () => {
  const urls = new Set([...(await sitemapPages()).values()].flat());
  // Check both ends of the actual catalog, including historical departments.
  for (const subject of ["COMPSCI", "MATH", "HEBR-MOD", ""]) {
    const request = new URL("https://uwcourses.com/search?ranking=easiest");
    if (subject) request.searchParams.set("subject", subject);
    const results = await search(request);
    const path = subject
      ? `/departments/${subject}/easiest`
      : "/courses/easiest";
    expect(urls.has(path)).toBe(results.total > 0);
    expect(
      pageSeo({ subject, collection: "easiest", results }, path).noindex,
    ).toBe(results.total === 0);
  }
});

it("does not invent missing catalog descriptions or promote unnamed instructor records", () => {
  const seo = pageSeo(
    {
      course: { course_id: "MATH 999", title: "Research", subjects: ["MATH"] },
    },
    "/courses/MATH_999",
  );
  expect(seo.noindex).toBe(false);
  expect(
    seo.structuredData["@graph"].some(
      (item: any) => item["@type"] === "Course",
    ),
  ).toBe(false);
  expect(
    pageSeo(
      { instructor: { name: null, instructor_url: "/instructors/UNKNOWN" } },
      "/instructors/UNKNOWN",
    ),
  ).toMatchObject({
    noindex: true,
    title: "Instructor record — Courses & Reviews | UW–Madison",
  });
});

it("normalizes equivalent path encodings to one canonical spelling", () => {
  expect(absoluteUrl("/departments/ANAT&PHY")).toBe(
    "https://uwcourses.com/departments/ANAT%26PHY",
  );
  expect(absoluteUrl("/departments/ANAT%26PHY")).toBe(
    absoluteUrl("/departments/ANAT&PHY"),
  );
  expect(() => absoluteUrl("/bad%path")).not.toThrow();
});
