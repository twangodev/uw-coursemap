export interface InstructorTrend {
  uid: string;
  name: string;
  count: number;
  terms: { term: string; gpa: number; count: number }[];
}
const grades = ["a", "ab", "b", "bc", "c", "d", "f"];
const weights = [4, 3.5, 3, 2.5, 2, 1, 0];
export function instructorSeries(rows: Record<string, any>[], names: Map<string, string>): InstructorTrend[] {
  const series = new Map<string, InstructorTrend>();
  for (const row of rows) {
    const counts = grades.map((grade) => Number(row[grade]) || 0);
    const count = counts.reduce((sum, n) => sum + n, 0);
    if (!count) continue;
    const current: InstructorTrend = series.get(row.instructor_uid) || { uid: row.instructor_uid, name: names.get(row.instructor_uid) || "Unknown instructor", count: 0, terms: [] };
    current.count += count;
    current.terms.push({ term: row.term, count, gpa: counts.reduce((sum, n, i) => sum + n * weights[i], 0) / count });
    series.set(row.instructor_uid, current);
  }
  return [...series.values()].sort((a, b) => b.count - a.count || a.uid.localeCompare(b.uid));
}
export function instructorChartRows(overall: { term: string; gpa: number | null }[], instructors: InstructorTrend[]) {
  const rows = new Map(overall.map((row) => [row.term, { term: row.term, overall: row.gpa } as Record<string, any>]));
  for (const instructor of instructors) for (const point of instructor.terms) {
    const row = rows.get(point.term) || { term: point.term, overall: null };
    row[instructor.uid] = point.gpa;
    rows.set(point.term, row);
  }
  return [...rows.values()].sort((a, b) => a.term.localeCompare(b.term)).map((row) => {
    for (const instructor of instructors) row[instructor.uid] ??= null;
    return row;
  });
}

/** Fit recorded GPA values with padding, including constant series and scale endpoints. */
export function gradeTrendDomain(rows: Record<string, unknown>[], keys: string[]): [number, number] {
  const values = rows.flatMap((row) => keys.map((key) => row[key]))
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (!values.length) return [0, 4];
  const low = Math.min(...values), high = Math.max(...values);
  const padding = Math.max(0.1, (high - low) * 0.12);
  return [Math.max(0, Math.floor((low - padding) * 20) / 20), Math.min(4, Math.ceil((high + padding) * 20) / 20)];
}
