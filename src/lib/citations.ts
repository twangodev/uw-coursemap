import type { Citation } from "./types";
export const citationContext = Symbol("course-citations");
export function citationKey(citation: Citation) {
  return citation.type === "review"
    ? `review:${citation.source_review_id || citation.review_id || citation.source_url}`
    : JSON.stringify([citation.type, citation.course_id, citation.term_id, citation.table, citation.section_number, citation.run_id]);
}
export function citationNumbers(summary: unknown) {
  const numbers = new Map<string, number>();
  function visit(value: unknown) {
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value)) { value.forEach(visit); return; }
    const record = value as Record<string, unknown>;
    if (Array.isArray(record.citations)) for (const citation of record.citations) {
      const key = citationKey(citation);
      if (!numbers.has(key)) numbers.set(key, numbers.size + 1);
    }
    Object.entries(record).filter(([key]) => key !== "citations").forEach(([, child]) => visit(child));
  }
  visit(summary);
  return numbers;
}
const reviewFiles = new Map<string, Promise<any[]>>();
export async function citedReviews(files: string[]) {
  return (await Promise.all(files.map((url) => {
    let pending = reviewFiles.get(url);
    if (!pending) {
      pending = fetch(url).then(async (response) => {
        if (!response.ok) throw new Error("This source could not be loaded. Please try again.");
        const rows = await response.json();
        if (!Array.isArray(rows)) throw new Error("This source file is invalid. Please try again.");
        return rows;
      }).catch((error) => { reviewFiles.delete(url); throw error; });
      if (reviewFiles.size >= 32) reviewFiles.delete(reviewFiles.keys().next().value!);
      reviewFiles.set(url, pending);
    }
    return pending;
  }))).flat();
}
