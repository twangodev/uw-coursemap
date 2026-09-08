import { normalize, courseUrl } from "./format";
import type { Requirements } from "./types";
export interface MapCourse {
  uid: string;
  code: string;
  title: string;
  subjects: string[];
}
export interface CourseMapData {
  courses: MapCourse[];
  edges: { source: string; target: string }[];
}
/** Course references only. Exclusion branches are not prerequisite edges. */
export function buildCourseMap(
  rows: (MapCourse & { requirements: Requirements | null })[],
): CourseMapData {
  const aliases = new Map<string, Set<string>>();
  for (const row of rows)
    for (const code of [
      row.code,
      ...row.subjects.map(
        (subject) => `${subject} ${row.code.split(" ").at(-1)}`,
      ),
    ]) {
      const key = normalize(code);
      if (!aliases.has(key)) aliases.set(key, new Set());
      aliases.get(key)!.add(row.uid);
    }
  const edges = new Map<string, { source: string; target: string }>();
  for (const row of rows) {
    const ast = row.requirements;
    if (!ast?.nodes?.length) continue;
    const nodes = new Map(ast.nodes.map((node) => [node.id, node]));
    const seen = new Set<string>();
    function visit(id: string) {
      if (seen.has(id)) return;
      seen.add(id);
      const node = nodes.get(id);
      if (!node || node.kind === "not") return;
      if (node.course) {
        const key = normalize(
          `${node.course.subjects.join("/")} ${node.course.course_number}`,
        );
        const matches =
          aliases.get(key) ||
          new Set(
            node.course.subjects.flatMap((subject) => [
              ...(aliases.get(
                normalize(`${subject} ${node.course!.course_number}`),
              ) || []),
            ]),
          );
        if (matches.size === 1) {
          const source = [...matches][0];
          if (source !== row.uid)
            edges.set(`${source}:${row.uid}`, { source, target: row.uid });
        }
      }
      for (const child of node.children || []) visit(child);
    }
    visit(ast.root);
  }
  return {
    courses: rows.map(({ requirements, ...row }) => row),
    edges: [...edges.values()],
  };
}
export function mapView(data: CourseMapData, focus: string) {
  const visible = new Set([focus]);
  for (const edge of data.edges)
    if (edge.source === focus || edge.target === focus) {
      visible.add(edge.source);
      visible.add(edge.target);
    }
  const courses = data.courses.filter((course) => visible.has(course.uid));
  const columns = [0, 0, 0];
  const result = {
    nodes: courses.map((course) => {
      const column =
        course.uid === focus
          ? 1
          : data.edges.some(
                (edge) => edge.source === course.uid && edge.target === focus,
              )
            ? 0
            : 2;
      return {
        id: course.uid,
        type: "course",
        position: { x: column * 320, y: columns[column]++ * 120 },
        data: {
          ...course,
          href: courseUrl(course.code),
          focused: course.uid === focus,
        },
      };
    }),
    edges: data.edges
      .filter((edge) => visible.has(edge.source) && visible.has(edge.target))
      .map((edge) => ({
        ...edge,
        id: `${edge.source}:${edge.target}`,
        type: "default",
        markerEnd: { type: "arrowclosed" as const },
      })),
  };
  for (const node of result.nodes) {
    const column = Math.round(node.position.x / 320);
    node.position.y -= (columns[column] - 1) * 60;
  }
  return result;
}
