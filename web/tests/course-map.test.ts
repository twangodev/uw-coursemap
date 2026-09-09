import { expect, it } from "vitest";
import { buildCourseMap } from "../../src/lib/course-map";
const course = (uid: string, code: string, requirements: any = null) => ({
  uid,
  code,
  title: code,
  subjects: ["COMPSCI"],
  requirements,
});
it("maps referenced alternatives, excludes exclusions, and handles cycles", () => {
  const ast = {
    root: "root",
    nodes: [
      { id: "root", kind: "any", children: ["a", "no", "root"] },
      {
        id: "a",
        kind: "course",
        children: [],
        course: { subjects: ["COMPSCI"], course_number: 200 },
      },
      { id: "no", kind: "not", children: ["b"] },
      {
        id: "b",
        kind: "course",
        children: [],
        course: { subjects: ["COMPSCI"], course_number: 367 },
      },
    ],
  };
  const map = buildCourseMap([
    course("200", "COMPSCI 200"),
    course("300", "COMPSCI 300", ast),
    course("367", "COMPSCI 367"),
  ]);
  expect(map.edges).toEqual([{ source: "200", target: "300" }]);
  expect(map.courses.map((node) => node.uid)).toEqual([
    "200",
    "300",
    "367",
  ]);
});
it("does not merge ambiguous courses or drop isolated course nodes", () => {
  const map = buildCourseMap([
    course("x", "COMPSCI 200"),
    course("y", "COMPSCI 200"),
    course("z", "COMPSCI 300", {
      root: "n",
      nodes: [
        {
          id: "n",
          children: [],
          kind: "course",
          course: { subjects: ["COMPSCI"], course_number: 200 },
        },
      ],
    }),
  ]);
  expect(map.edges).toEqual([]);
  expect(map.courses.map(node => node.uid)).toEqual(["x", "y", "z"]);
});
