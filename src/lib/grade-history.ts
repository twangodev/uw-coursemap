import { termName } from "./format";
export const letterGrades = ["a", "ab", "b", "bc", "c", "d", "f"];
export const otherGrades = [
  "satisfactory",
  "unsatisfactory",
  "credit",
  "no_credit",
  "passed",
  "incomplete",
  "no_work",
  "not_reported",
  "other",
];
/** Whole-course or selected-instructor records, already reconciled by the importer. */
export function gradeHistory(records: Record<string, any>[], through = "") {
  const terms = new Map<string, Record<string, any>>();
  for (const record of records) {
    if (through && record.term_id > through) continue;
    const row = terms.get(record.term_id) || {
      term: record.term_id,
      label: termName(record.term_id),
      total: 0,
      letters: 0,
      nonLetter: 0,
    };
    for (const key of [...letterGrades, ...otherGrades])
      row[key] = (row[key] || 0) + Math.max(0, Number(record[key]) || 0);
    terms.set(record.term_id, row);
  }
  return [...terms.values()]
    .sort((a, b) => a.term.localeCompare(b.term))
    .map((row) => {
      row.letters = letterGrades.reduce((sum, key) => sum + row[key], 0);
      row.nonLetter = otherGrades.reduce((sum, key) => sum + row[key], 0);
      row.total = row.letters + row.nonLetter;
      for (const key of letterGrades)
        row[key + "Share"] = row.total ? (row[key] / row.total) * 100 : 0;
      row.nonLetterShare = row.total ? (row.nonLetter / row.total) * 100 : 0;
      return row;
    })
    .filter((row) => row.total > 0);
}
