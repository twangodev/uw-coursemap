import { z } from "zod";

const count = z.number().int().nonnegative();
export const schoolTermSchema = z.object({
  courses: count,
  instructors: count,
  sections: count,
  lectures: count,
  knownLectures: count,
  medianLecture: z.number().nullable(),
  sizes: z.array(z.object({ label: z.string(), count })),
  largest: z.array(
    z.object({ code: z.string(), title: z.string(), enrolled: count }),
  ),
  grades: z.array(count).length(7),
  gradeCount: count,
  gpa: z.number().nullable(),
  schedule: z.object({
    from: z.string().nullable(),
    through: z.string().nullable(),
    meetings: count,
    cells: z.array(z.object({ day: count, hour: count, meetings: count })),
    buildings: z.array(
      z.object({
        name: z.string(),
        latitude: z.number(),
        longitude: z.number(),
        meetings: count,
        enrolledVisits: count,
        knownMeetings: count,
      }),
    ),
  }),
});
export const schoolStatsSchema = z.object({
  selectedTerm: z.string(),
  terms: z.record(z.string(), schoolTermSchema),
});
export type SchoolTerm = z.infer<typeof schoolTermSchema>;
export type SchoolStats = z.infer<typeof schoolStatsSchema>;
export const gradeLabels = ["A", "AB", "B", "BC", "C", "D", "F"];
export function gradeTotals(counts: number[]) {
  const count = counts.reduce((a, b) => a + b, 0);
  return {
    gradeCount: count,
    gpa: count
      ? counts.reduce(
          (sum, n, i) => sum + n * [4, 3.5, 3, 2.5, 2, 1, 0][i],
          0,
        ) / count
      : null,
  };
}
export function lectureSizes(values: number[]) {
  const sorted = values
    .filter((n) => Number.isFinite(n) && n >= 0)
    .sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return {
    knownLectures: sorted.length,
    medianLecture: sorted.length
      ? sorted.length % 2
        ? sorted[mid]
        : (sorted[mid - 1] + sorted[mid]) / 2
      : null,
    sizes: [20, 50, 100, 200, 500, Infinity].map((upper, i, limits) => ({
      label: ["Under 20", "20–49", "50–99", "100–199", "200–499", "500+"][i],
      count: sorted.filter((n) => n >= (limits[i - 1] ?? 0) && n < upper)
        .length,
    })),
  };
}
export function emptySchoolTerm(): SchoolTerm {
  return {
    courses: 0,
    instructors: 0,
    sections: 0,
    lectures: 0,
    ...lectureSizes([]),
    largest: [],
    grades: [0, 0, 0, 0, 0, 0, 0],
    ...gradeTotals([]),
    schedule: {
      from: null,
      through: null,
      meetings: 0,
      cells: [],
      buildings: [],
    },
  };
}
export function gradedTerm(stats: SchoolStats, selected: string) {
  return (
    Object.keys(stats.terms)
      .filter((t) => t <= selected && stats.terms[t].gradeCount > 0)
      .sort()
      .at(-1) ?? null
  );
}
