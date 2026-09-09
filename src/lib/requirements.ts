import type { Requirements, RequirementNode } from "./types";
export function nodeLabel(n: Pick<RequirementNode, "kind" | "course" | "condition" | "evidence">) {
  if (n.course)
    return `${n.course.subjects.join("/")} ${n.course.course_number}${n.course.minimum_grade ? " · " + n.course.minimum_grade : ""}${n.course.timing && n.course.timing !== "prior" ? " · " + n.course.timing : ""}`;
  return requirementText(
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
export type RequirementBranch = Omit<RequirementNode, "children"> & { children: RequirementBranch[] };

export function requirementTree(ast: Requirements): RequirementBranch | null {
  const nodes = new Map(ast.nodes.map(node => [node.id, node]));
  function visit(id: string, ancestors: Set<string>): RequirementBranch | null {
    const node = nodes.get(id);
    if (!node || ancestors.has(id)) return null;
    const path = new Set([...ancestors, id]);
    return { ...node, children: (node.children || []).map(child => visit(child, path)).filter((child): child is RequirementBranch => child !== null) };
  }
  return visit(ast.root, new Set());
}

/** Repair whitespace lost between catalog HTML nodes without rewriting requirements. */
export function requirementText(text: string): string {
  return text.replace(/\s+/g, " ")
    .replace(/\b(or|and)(?=\d{3}\b)/g, "$1 ")
    .replace(/(\d{3})(?=(?:or|and|does|do|is|are)\b)/g, "$1 ")
    .replace(/(\d{3})(or|and)(?=\d{3}\b)/g, "$1 $2 ")
    .replace(/(\d{3})(and|or)(?=[A-Z])/g, "$1 $2 ")
    .replace(/\b(into|and|or)(?=[A-Z]{2})/g, "$1 ")
    .replace(/(\b\d{3}),(?=\d{3}\b)/g, "$1, ")
    .replace(/([.;])(?=[A-Z])/g, "$1 ")
    .trim();
}
