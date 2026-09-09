import { expect, it } from "vitest";
import { cardFromHtml } from "../social-images.mjs";
function html(graph: any[], path = "/social/pages/courses/COMPSCI_300.png") {
  return `<meta property="og:image" content="https://uwcourses.com${path}"><script type="application/ld+json">${JSON.stringify({ "@graph": graph })}</script>`;
}
it("uses course identity and literal text, not promotional page titles", () => {
  expect(
    cardFromHtml(
      html([
        { "@type": "WebPage", name: "CS 300 | UW" },
        {
          "@type": "Course",
          courseCode: "COMPSCI 300",
          name: "Programming <II> & more",
        },
      ]),
    ),
  ).toMatchObject({ label: "COMPSCI 300", title: "Programming <II> & more" });
});
it("keeps department cards to the actual department name", () => {
  expect(
    cardFromHtml(
      html(
        [
          {
            "@type": "CollectionPage",
            name: "Computer Sciences Courses, Grades & Reviews | UW",
          },
          {
            "@type": "BreadcrumbList",
            itemListElement: [
              {
                item: "https://uwcourses.com/departments/COMPSCI",
                name: "Computer Sciences",
              },
            ],
          },
        ],
        "/social/pages/departments/COMPSCI.png",
      ),
    ),
  ).toMatchObject({ label: "Department", title: "Computer Sciences" });
});
it("skips fallback images and pages without indexable page entities", () => {
  expect(cardFromHtml(html([], "/social/courses.png"))).toBeNull();
  expect(cardFromHtml(html([]))).toBeNull();
});
