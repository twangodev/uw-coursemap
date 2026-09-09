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
    expect(seo.structuredData["@graph"]).toHaveLength(3);
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
    urls.some((path) => /[?#]|^\/stats|^\/subjects|course_/.test(path)),
  ).toBe(false);
  expect(urls).toContain("/search");
  expect(urls).toContain("/instructors/by-rating-count");
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
}, 30_000);

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

it("connects instructor pages to their own Person records without asserting affiliation", () => {
  const records = [
    "/instructors/EXAMPLE_NAME",
    "/instructors/EXAMPLE_NAME--other",
  ];
  const ids = records.map((path) => {
    const seo = pageSeo(
      { instructor: { name: "Example Name", instructor_url: path } },
      path,
    );
    const person = seo.structuredData["@graph"].find(
      (item) => item["@type"] === "Person",
    )!;
    const page = seo.structuredData["@graph"].find(
      (item) => item["@type"] === "WebPage",
    )!;
    expect(person).toEqual({
      "@type": "Person",
      "@id": seo.canonical + "#person",
      name: "Example Name",
      url: seo.canonical,
    });
    expect(page.mainEntity).toEqual({ "@id": person["@id"] });
    expect(page.name).toBe(seo.title);
    expect(
      seo.structuredData["@graph"].some(
        (item) => item["@type"] === "ProfilePage",
      ),
    ).toBe(false);
    return person["@id"];
  });
  expect(new Set(ids).size).toBe(2);
});

it("gives every indexable page family a connected page entity", () => {
  for (const [path, data] of [
    ["/", {}],
    ["/departments", {}],
    ["/explorer/all", {}],
    [
      "/courses/MATH_221",
      {
        course: {
          course_id: "MATH 221",
          title: "Calculus",
          description: "Differential calculus",
          subjects: ["MATH"],
        },
      },
    ],
    [
      "/departments/MATH/catalog",
      { subject: "MATH", catalog: [{ course_id: "MATH 221" }] },
    ],
  ] as const) {
    const seo = pageSeo(data, path);
    const graph = seo.structuredData["@graph"];
    const page = graph.find((item) =>
      ["WebPage", "CollectionPage"].includes(String(item["@type"])),
    )!;
    expect(page).toMatchObject({
      "@id": seo.canonical + "#webpage",
      url: seo.canonical,
      description: seo.description,
      isPartOf: { "@id": "https://uwcourses.com/#website" },
    });
    for (const relation of [page.mainEntity, page.breadcrumb])
      if (relation)
        expect(
          graph.some((item) => item["@id"] === (relation as any)["@id"]),
        ).toBe(true);
  }
  expect(pageSeo({}, "/missing", 404).structuredData["@graph"]).toEqual([]);
});

it("indexes clean discovery pages with distinct metadata, but excludes filtered results", () => {
  for (const path of ["/search", "/instructors/by-rating-count"]) {
    const seo = pageSeo({ discoveryFiltered: false }, path);
    expect(seo.noindex).toBe(false);
    expect(seo.canonical).toBe("https://uwcourses.com" + path);
    expect(
      seo.structuredData["@graph"].some(
        (item) => item["@type"] === "CollectionPage",
      ),
    ).toBe(true);
    expect(pageSeo({ discoveryFiltered: true }, path).noindex).toBe(true);
    expect(pageSeo({ discoveryFiltered: false }, path, 404).noindex).toBe(true);
  }
  expect(pageSeo({ discoveryFiltered: false }, "/search").title).not.toBe(
    pageSeo({ discoveryFiltered: false }, "/instructors/by-rating-count").title,
  );
});
