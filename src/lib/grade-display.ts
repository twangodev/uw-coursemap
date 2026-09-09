import { gradeKeys } from "./grade-projection";

/** Keep the page's selected term while choosing the grades available to show. */
export function gradeDisplay(
  grades: { term_id: string; [key: string]: unknown }[],
  selectedTerm: string,
  projectedTerm: string,
  hasInterval: boolean,
) {
  const pending = !!projectedTerm && selectedTerm === projectedTerm;
  if (!pending) return { mode: "recorded", term: selectedTerm } as const;
  if (hasInterval) return { mode: "projected", term: selectedTerm } as const;
  const latest = grades
    .filter(
      (row) =>
        row.term_id < selectedTerm &&
        gradeKeys.some((key) => Number(row[key]) > 0),
    )
    .map((row) => row.term_id)
    .sort()
    .at(-1);
  return latest
    ? ({ mode: "fallback", term: latest } as const)
    : ({ mode: "empty", term: selectedTerm } as const);
}
