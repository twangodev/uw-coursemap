import type { AcademicCourse } from "./school-academics";
import { subjectVolumes } from "./school-academics";

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
  const featuredCourses = new Set(ranked.slice(0, 8).map((c) => c.code));
  const featuredSubjects = new Set(
    subject
      ? [subject]
      : subjectVolumes(courses)
          .slice(0, 6)
          .map((s) => s.subject),
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
    const featured = featuredCourses.has(c.code);
    const courseId = add({
      id: featured ? `course:${c.code}` : "courses:other",
      label: featured ? c.code : "Other courses",
      kind: "course",
      code: featured ? c.code : undefined,
      color: "#a58b82",
    });
    const subjects = c.subjects.length ? c.subjects : ["OTHER"];
    for (const s of subjects) {
      if (subject && s !== subject) continue;
      const featured = featuredSubjects.has(s);
      const id = add({
        id: featured ? `subject:${s}` : "subjects:other",
        label: featured ? s : "Other departments",
        kind: "subject",
        subject: featured ? s : undefined,
        color: "#bd5047",
      });
      link(id, courseId, c.count / subjects.length);
    }
    gradeBands.forEach((band, i) => {
      const count =
        band.indices.reduce((sum, index) => sum + c.grades[index], 0) *
        weight(c);
      if (!count) return;
      const id = add({
        id: `grade:${i}`,
        label: band.label,
        kind: "grade",
        color: band.color,
      });
      link(courseId, id, count);
    });
  }
  return {
    nodes: [...nodes.values()],
    links: [...links.values()],
    total: ranked.reduce((sum, c) => sum + c.count * weight(c), 0),
    courseCount: ranked.length,
  };
}
