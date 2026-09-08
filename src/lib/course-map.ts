import { normalize } from "./format";
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
