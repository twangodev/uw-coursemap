import { expect, it } from "vitest";
import { academicTerms } from "../../src/lib/school-academics";
import { gradeFlow, flowPage } from "../../src/lib/school-sankey";

const rows = Array.from({ length: 12 }, (_, i) => ({
  uid: `${i}`,
  term: "1264",
  a: i + 1,
  ab: 2,
  b: 3,
  bc: 4,
  c: 5,
  d: 6,
  f: 7,
}));
const courses = academicTerms(
  rows,
  rows.map((r, i) => ({
    uid: r.uid,
    code: `COURSE ${i}`,
    title: "Test",
    subjects: i === 0 ? ["CS", "ECE"] : [`SUBJECT${i}`],
  })),
)["1264"];

it("retains actual grade bins and conserves volume through complete and cross-listed flows", () => {
  expect(courses.find((c) => c.code === "COURSE 0")!.grades).toEqual([
    1, 2, 3, 4, 5, 6, 7,
  ]);
  const graph = gradeFlow(courses);
  expect(graph.nodes.filter((n) => n.kind === "subject")).toHaveLength(13);
  expect(graph.nodes.filter((n) => n.kind === "course")).toHaveLength(0);
  expect(graph.total).toBe(courses.reduce((sum, c) => sum + c.count, 0));
  const total = (kind: string) =>
    graph.nodes
      .filter((n) => n.kind === kind)
      .reduce(
        (sum, n) =>
          sum +
          graph.links
            .filter((l) =>
              kind === "grade" ? l.target === n.id : l.source === n.id,
            )
            .reduce((s, l) => s + l.value, 0),
        0,
      );
  expect(total("subject")).toBeCloseTo(graph.total);
  expect(graph.nodes.some((n) => n.label.startsWith("Other "))).toBe(false);
  expect(total("grade")).toBeCloseTo(graph.total);
  for (const node of graph.nodes.filter((n) => n.kind === "course")) {
    const incoming = graph.links
      .filter((l) => l.target === node.id)
      .reduce((s, l) => s + l.value, 0);
    const outgoing = graph.links
      .filter((l) => l.source === node.id)
      .reduce((s, l) => s + l.value, 0);
    expect(incoming).toBeCloseTo(outgoing);
  }
  expect(
    graph.links
      .filter((l) => l.target === "grade:0")
      .reduce((s, l) => s + l.value, 0),
  ).toBe(rows.reduce((s, r) => s + r.a + r.ab, 0));
});
it("drills into a department without doubling cross-listed grades or mutating the source", () => {
  const graph = gradeFlow(courses, "CS");
  expect(graph.total).toBe(14);
  expect(graph.courseCount).toBe(1);
  expect(
    graph.nodes.filter((n) => n.kind === "subject").map((n) => n.subject),
  ).toEqual(["CS"]);
  expect(graph.links.find((l) => l.target === "grade:0")!.value).toBe(1.5);
  expect(courses.find((c) => c.code === "COURSE 0")!.count).toBe(28);
  expect(gradeFlow(courses, "missing").links).toEqual([]);
  expect(gradeFlow([]).nodes).toEqual([]);
});
it("does not invent zero-grade bands", () => {
  const graph = gradeFlow([
    {
      code: "A 1",
      title: "A",
      subjects: [],
      count: 5,
      gpa: 4,
      grades: [5, 0, 0, 0, 0, 0, 0],
    },
  ]);
  expect(
    graph.nodes.filter((n) => n.kind === "grade").map((n) => n.label),
  ).toEqual(["A / AB"]);
  expect(graph.links.every((l) => l.value > 0)).toBe(true);
  expect(
    gradeFlow(
      [
        {
          code: "A 1",
          title: "A",
          subjects: [],
          count: 5,
          gpa: 4,
          grades: [5, 0, 0, 0, 0, 0, 0],
        },
      ],
      "OTHER",
    ).total,
  ).toBe(5);
});

it("includes every course when drilling into a large department", () => {
  const all = courses.map((c) => ({ ...c, subjects: ["CS"] }));
  const graph = gradeFlow(all, "CS");
  expect(graph.nodes.filter((n) => n.kind === "course")).toHaveLength(
    all.length,
  );
  for (const node of graph.nodes.filter((n) => n.kind === "course")) {
    const incoming = graph.links
      .filter((l) => l.target === node.id)
      .reduce((s, l) => s + l.value, 0);
    const outgoing = graph.links
      .filter((l) => l.source === node.id)
      .reduce((s, l) => s + l.value, 0);
    expect(incoming).toBeCloseTo(outgoing);
  }
});

it("pages every named flow without hiding volume in an aggregate", () => {
  for (const subject of ["", "CS"]) {
    const graph = gradeFlow(
      subject ? courses.map((c) => ({ ...c, subjects: ["CS"] })) : courses,
      subject,
    );
    const first = flowPage(graph, subject, 0, 5);
    let total = 0;
    const names = [];
    for (let p = 0; p < first.pages; p++) {
      const view = flowPage(graph, subject, p, 5);
      total += view.total;
      names.push(
        ...view.nodes
          .filter((n) => n.kind === (subject ? "course" : "subject"))
          .map((n) => n.id),
      );
      expect(
        view.links.every(
          (l) =>
            view.nodes.some((n) => n.id === l.source) &&
            view.nodes.some((n) => n.id === l.target),
        ),
      ).toBe(true);
    }
    expect(total).toBeCloseTo(graph.total);
    expect(new Set(names).size).toBe(names.length);
    expect(names.length).toBe(first.count);
  }
});
