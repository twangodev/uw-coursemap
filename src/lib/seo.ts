import { courseTitle, courseUrl } from "$lib/format";
import { departmentName } from "$lib/departments";
import {
  courseCollections,
  type CourseCollection,
} from "$lib/course-collections";

export const siteOrigin = "https://uwcourses.com";
export function absoluteUrl(path: string) {
  // Never inherit a preview host, query string, or fragment as the canonical.
  return (
    siteOrigin +
    new URL(path, siteOrigin).pathname
      .split("/")
      .map((segment) => {
        try {
          return encodeURIComponent(decodeURIComponent(segment));
        } catch {
          return encodeURIComponent(segment);
        }
      })
      .join("/")
  );
}
export function jsonLd(value: unknown) {
  return JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}
function snippet(value: string, limit = 160) {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length <= limit
    ? text
    : text.slice(0, limit - 1).replace(/\s+\S*$/, "") + "…";
}
export function courseSchema(course: any) {
  return {
    "@type": "Course",
    "@id": absoluteUrl(courseUrl(course.course_id)) + "#course",
    url: absoluteUrl(courseUrl(course.course_id)),
    name: courseTitle(course.title),
    courseCode: course.course_id,
    description: course.description || undefined,
    coursePrerequisites: course.requirements_text || undefined,
    provider: {
      "@type": "CollegeOrUniversity",
      name: "University of Wisconsin–Madison",
      url: "https://www.wisc.edu/",
    },
  };
}
export function breadcrumbs(items: { name: string; path: string }[]) {
  return {
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}
export function pageSeo(data: any, pathname: string, status = 200) {
  let path = pathname;
  let title = "UW–Madison Courses, Grades & Prerequisites | UW Courses";
  let description =
    "Explore UW–Madison courses, prerequisites, historical grade distributions and instructor reviews. Find classes for your next semester.";
  const graph: Record<string, unknown>[] = [];
  const noindex =
    status >= 400 ||
    ((pathname === "/search" || pathname === "/instructors/by-rating-count") && data.discoveryFiltered !== false) ||
    Boolean(data.collection && data.results?.total === 0) ||
    Boolean(data.instructor && !data.instructor.name?.trim());
  if (status >= 400) {
    title = `${status === 404 ? "Page not found" : "Page unavailable"} | UW Courses`;
    description =
      "This page is unavailable. Browse UW–Madison courses by department.";
  } else if (data.course) {
    const c = data.course;
    path = courseUrl(c.course_id);
    title = `${c.course_id}: ${courseTitle(c.title)} | UW–Madison`;
    description = snippet(
      `${c.course_id} at UW–Madison: ${courseTitle(c.title)}. Prerequisites, credits, historical grades and instructors. ${c.description || ""}`,
    );
    graph.push(
      ...(c.description?.trim() ? [courseSchema(c)] : []),
      breadcrumbs([
        { name: "Departments", path: "/departments" },
        ...(c.subjects?.length
          ? [
              {
                name: departmentName(c.subjects[0]),
                path: `/departments/${encodeURIComponent(c.subjects[0])}`,
              },
            ]
          : []),
        { name: c.course_id, path },
      ]),
    );
  } else if (data.instructor) {
    const i = data.instructor;
    path = i.instructor_url;
    if (!noindex)
      graph.push({
        "@type": "Person",
        "@id": absoluteUrl(path) + "#person",
        name: i.name,
        url: absoluteUrl(path),
      });
    title = `${i.name || "Instructor record"} — Courses & Reviews | UW–Madison`;
    description = snippet(
      `Courses taught by ${i.name || "this instructor"} at UW–Madison. Explore student reviews, historical grades and teaching history.`,
    );
  } else if (data.collection) {
    const collection = courseCollections[data.collection as CourseCollection];
    title = `${collection.title}${data.subject ? ` in ${departmentName(data.subject)}` : ""} | UW–Madison`;
    description = snippet(
      `${collection.description} Compare historical grades for ${data.subject ? departmentName(data.subject) : "UW–Madison"} courses. Grades reflect past outcomes, not workload.`,
    );
  } else if (data.subject) {
    const name = departmentName(data.subject);
    const catalog = pathname.endsWith("/catalog");
    const map = pathname.startsWith("/explorer/");
    title = `${name} ${map ? "Prerequisite Map" : catalog ? "Course Catalog" : "Courses, Grades & Reviews"} | UW–Madison`;
    description = snippet(
      `Browse ${name} (${data.subject}) courses at UW–Madison. Explore ${catalog ? "the full recorded catalog, including courses not offered this term" : "prerequisites, historical grades and instructor reviews"}.`,
    );
    if (!map)
      graph.push(
        breadcrumbs([
          { name: "Departments", path: "/departments" },
          { name, path: `/departments/${encodeURIComponent(data.subject)}` },
          ...(catalog ? [{ name: "Course catalog", path }] : []),
        ]),
      );
  } else if (pathname === "/departments") {
    title = "UW–Madison Departments & Course Catalog | UW Courses";
    description =
      "Browse all UW–Madison departments and their course catalogs. Find prerequisites, credits, historical grades and instructor reviews.";
  } else if (pathname.startsWith("/explorer")) {
    title = "UW–Madison Course Prerequisite Maps | UW Courses";
    description =
      "Explore UW–Madison course prerequisites and see how classes connect across departments.";
  } else if (
    pathname === "/search" ||
    pathname === "/instructors/by-rating-count"
  ) {
    const instructors = pathname === "/instructors/by-rating-count";
    title = instructors
      ? "UW–Madison Professors, Ratings & Reviews | UW Courses"
      : "Explore UW–Madison Courses, Grades & Prerequisites | UW Courses";
    description = instructors
      ? "Find UW–Madison professors and compare student reviews, instructor ratings, courses taught and historical grades."
      : "Discover UW–Madison courses for your next semester. Compare prerequisites, historical grades and instructors, and explore courses by department.";
  }
  if (pathname === "/" && status < 400)
    graph.push({
      "@type": "WebSite",
      "@id": siteOrigin + "/#website",
      name: "UW Courses",
      alternateName: "UW Course Map",
      url: siteOrigin + "/",
      description,
    });
  // Only annotate links present in the rendered list, never unseen result pages.
  const courses = data.catalog || data.results?.items;
  if (
    !noindex &&
    courses?.length &&
    (data.catalog || data.subject || data.collection)
  ) {
    const items = courses.filter((c: any) => c.course_id);
    if (items.length)
      graph.push({
        "@type": "ItemList",
        "@id": absoluteUrl(path) + "#courses",
        itemListElement: items.map((c: any, i: number) => ({
          "@type": "ListItem",
          position: i + 1,
          url: absoluteUrl(courseUrl(c.course_id)),
        })),
      });
  }
  const canonical = absoluteUrl(path);
  const imageKind = pathname.startsWith("/explorer") ? "maps"
    : pathname.startsWith("/instructors") ? "instructors"
    : data.subject && !data.course ? "departments"
    : pathname === "/departments" ? "departments" : "courses";
  const imageDescriptions = {
    courses: "UW Courses — Find your next favorite class. Courses, grades and prerequisites.",
    instructors: "UW Courses — Know your professors. Student reviews and teaching history.",
    departments: "UW Courses — Explore every possibility. Departments, courses and connections.",
    maps: "UW Courses — See the connections. Explore your prerequisite paths.",
  };
  if (!noindex) {
    const entity = graph.find((item) =>
      ["Course", "Person", "ItemList"].includes(String(item["@type"])),
    );
    const breadcrumb = graph.find((item) => item["@type"] === "BreadcrumbList");
    if (breadcrumb) breadcrumb["@id"] = canonical + "#breadcrumb";
    graph.push({
      "@type":
        entity?.["@type"] === "ItemList" || pathname === "/departments" || pathname === "/search" || pathname === "/instructors/by-rating-count"
          ? "CollectionPage"
          : "WebPage",
      "@id": canonical + "#webpage",
      url: canonical,
      name: title,
      description,
      inLanguage: "en",
      isPartOf: { "@id": siteOrigin + "/#website" },
      ...(entity ? { mainEntity: { "@id": entity["@id"] } } : {}),
      ...(breadcrumb ? { breadcrumb: { "@id": breadcrumb["@id"] } } : {}),
    });
  }
  return {
    title,
    description,
    canonical,
    image: absoluteUrl(`/social/${imageKind}.png`),
    imageAlt: imageDescriptions[imageKind],
    noindex,
    structuredData: { "@context": "https://schema.org", "@graph": graph },
  };
}
