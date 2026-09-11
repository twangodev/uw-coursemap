import type { AcademicCourse } from "./school-academics";

export const gradeBands = [
  { label: "A / AB", color: "#3f927c", indices: [0, 1] },
  { label: "B / BC", color: "#799a62", indices: [2, 3] },
  { label: "C", color: "#cd923e", indices: [4] },
  { label: "D / F", color: "#bd5047", indices: [5, 6] },
];
export type FlowNode = {
  id: string;
  label: string;
  kind: "subject" | "course" | "grade";
  subject?: string;
  code?: string;
  color: string;
};
export type FlowLink = { source: string; target: string; value: number };

/** Every edge carries attributed letter grades, with identical totals at each layer. */
export function gradeFlow(courses: AcademicCourse[], subject = "") {
  const filtered = subject
    ? courses.filter((c) =>
        (c.subjects.length ? c.subjects : ["OTHER"]).includes(subject),
      )
    : courses;
  const weight = (c: AcademicCourse) =>
    subject ? 1 / Math.max(1, c.subjects.length) : 1;
  const ranked = [...filtered].sort(
    (a, b) =>
      b.count * weight(b) - a.count * weight(a) || a.code.localeCompare(b.code),
  );
  const nodes = new Map<string, FlowNode>();
  const links = new Map<string, FlowLink>();
  const add = (node: FlowNode) => {
    if (!nodes.has(node.id)) nodes.set(node.id, node);
    return node.id;
  };
  const link = (source: string, target: string, value: number) => {
    if (value <= 0) return;
    const key = JSON.stringify([source, target]);
    const edge = links.get(key) ?? { source, target, value: 0 };
    edge.value += value;
    links.set(key, edge);
  };
  for (const c of ranked) {
    const courseId = subject
      ? add({
          id: `course:${c.code}`,
          label: c.code,
          kind: "course",
          code: c.code,
          color: "#a58b82",
        })
      : null;
    const subjects = c.subjects.length ? c.subjects : ["OTHER"];
    for (const s of subjects) {
      if (subject && s !== subject) continue;
      const id = add({
        id: `subject:${s}`,
        label: s,
        kind: "subject",
        subject: s,
        color: "#bd5047",
      });
      if (courseId) link(id, courseId, c.count / subjects.length);
      gradeBands.forEach((band, i) => {
        const count =
          band.indices.reduce((sum, index) => sum + c.grades[index], 0) /
          subjects.length;
        if (!count) return;
        const gradeId = add({
          id: `grade:${i}`,
          label: band.label,
          kind: "grade",
          color: band.color,
        });
        link(courseId ?? id, gradeId, count);
      });
    }
  }
  return {
    nodes: [...nodes.values()],
    links: [...links.values()],
    total: ranked.reduce((sum, c) => sum + c.count * weight(c), 0),
    courseCount: ranked.length,
  };
}

/** A visible slice, never an “Other” aggregate; rebuild shared totals from its edges. */
export function flowPage(
  graph: ReturnType<typeof gradeFlow>,
  subject: string,
  page: number,
  size = 12,
) {
  const kind = subject ? "course" : "subject";
  const values = new Map<string, number>();
  for (const link of graph.links)
    values.set(link.source, (values.get(link.source) ?? 0) + link.value);
  const rows = graph.nodes
    .filter((n) => n.kind === kind)
    .sort(
      (a, b) =>
        (values.get(b.id) ?? 0) - (values.get(a.id) ?? 0) ||
        a.id.localeCompare(b.id),
    );
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const current = Math.max(0, Math.min(page, pages - 1));
  const start = current * size;
  const selected = new Set(rows.slice(start, start + size).map((n) => n.id));
  const links = graph.links.filter(
    (l) => selected.has(l.source) || selected.has(l.target),
  );
  const used = new Set(links.flatMap((l) => [l.source, l.target]));
  const nodes = graph.nodes.filter((n) => used.has(n.id));
  const grades = new Set(
    nodes.filter((n) => n.kind === "grade").map((n) => n.id),
  );
  return {
    nodes,
    links,
    pages,
    current,
    start,
    end: Math.min(start + size, rows.length),
    count: rows.length,
    total: links
      .filter((l) => grades.has(l.target))
      .reduce((s, l) => s + l.value, 0),
  };
}
