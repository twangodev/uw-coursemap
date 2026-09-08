import type { Requirements, RequirementNode } from "./types";
export function nodeLabel(n: RequirementNode) {
  if (n.course)
    return `${n.course.subjects.join("/")} ${n.course.course_number}${n.course.minimum_grade ? " · " + n.course.minimum_grade : ""}${n.course.timing && n.course.timing !== "prior" ? " · " + n.course.timing : ""}`;
  return (
    (
      { all: "All of", any: "Any of", not: "Not eligible with" } as Record<
        string,
        string
      >
    )[n.kind] ||
    n.condition ||
    n.evidence ||
    "Requirement"
  );
}
export function visibleTree(ast: Requirements, expanded: Set<string>) {
  const nodes: any[] = [],
    edges: any[] = [];
  const seen = new Set<string>();
  const byId = new Map(ast.nodes.map((n) => [n.id, n]));
  let y = 0;
  function walk(id: string, depth: number, parent?: string) {
    if (seen.has(id)) return;
    seen.add(id);
    const n = byId.get(id);
    if (!n) return;
    const entry = {
      id,
      type: "requirement",
      position: { x: depth * 260, y: 0 },
      data: {
        label: nodeLabel(n),
        course: n.course,
        expandable: !!n.children?.length,
        expanded: expanded.has(id),
      },
    };
    nodes.push(entry);
    if (parent)
      edges.push({ id: parent + "-" + id, source: parent, target: id });
    const start = nodes.length;
    if (expanded.has(id))
      for (const child of n.children || []) walk(child, depth + 1, id);
    const children = nodes
      .slice(start)
      .filter((child) =>
        edges.some((edge) => edge.source === id && edge.target === child.id),
      );
    entry.position.y = children.length
      ? (children[0].position.y + children[children.length - 1].position.y) / 2
      : y++ * 120;
  }
  walk(ast.root, 0);
  return { nodes, edges };
}
