import { z } from "zod";

const gradeCountSchema = z.number().int().nonnegative();

export const academicCourseSchema = z.object({
  code: z.string(),
  title: z.string(),
  subjects: z.array(z.string()),
  count: z.number().int().positive(),
  gpa: z.number().nullable(),
  // A, AB, B, BC, C, D, F: retain counts so flows never infer grades from GPA.
  grades: z.tuple([
    gradeCountSchema,
    gradeCountSchema,
    gradeCountSchema,
    gradeCountSchema,
    gradeCountSchema,
    gradeCountSchema,
    gradeCountSchema,
  ]),
});
export type AcademicCourse = z.infer<typeof academicCourseSchema>;
export const academicsSchema = z.object({
  term: z.string().nullable(),
  courses: z.array(academicCourseSchema),
  popularity: z.array(
    z.object({
      code: z.string(),
      title: z.string(),
      points: z.array(
        z.object({
          term: z.string(),
          rank: z.number().int().positive().nullable(),
          count: z.number().int().nonnegative(),
        }),
      ),
    }),
  ),
});
export type Academics = z.infer<typeof academicsSchema>;
export interface GradeCourseRow {
  uid: string;
  term: string;
  a: number;
  ab: number;
  b: number;
  bc: number;
  c: number;
  d: number;
  f: number;
}
export interface AcademicMetadata {
  uid: string;
  code: string;
  title: string;
  subjects: string[];
}
/** Each reconciled course/term contributes once; rankings never join subject aliases. */
export function academicTerms(
  rows: GradeCourseRow[],
  metadata: AcademicMetadata[],
) {
  const courses = new Map(metadata.map((c) => [c.uid, c]));
  const terms: Record<string, AcademicCourse[]> = {};
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.term}:${row.uid}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const course = courses.get(row.uid);
    if (!course) continue;
    const { gradeCount, gpa } = gradeTotals([
      row.a,
      row.ab,
      row.b,
      row.bc,
      row.c,
      row.d,
      row.f,
    ]);
    if (!gradeCount) continue;
    (terms[row.term] ??= []).push({
      code: course.code,
      title: course.title,
      subjects: [...new Set(course.subjects)].sort(),
      count: gradeCount,
      gpa,
      grades: [row.a, row.ab, row.b, row.bc, row.c, row.d, row.f],
    });
  }
  for (const term of Object.values(terms))
    term.sort((a, b) => b.count - a.count || a.code.localeCompare(b.code));
  return terms;
}
export function selectAcademics(
  terms: Record<string, AcademicCourse[]>,
  through: string,
): Academics {
  const dates = Object.keys(terms)
    .filter((t) => t <= through)
    .sort();
  const term = dates.at(-1) ?? null;
  if (!term) return { term: null, courses: [], popularity: [] };
  const window = dates.slice(-10);
  const ranks = new Map(
    window.map((t) => [
      t,
      new Map(
        terms[t].map((c, i) => [c.code, { rank: i + 1, count: c.count }]),
      ),
    ]),
  );
  return {
    term,
    courses: terms[term],
    popularity: terms[term].slice(0, 8).map((c) => ({
      code: c.code,
      title: c.title,
      points: window.map((t) => ({
        term: t,
        ...(ranks.get(t)!.get(c.code) ?? { rank: null, count: 0 }),
      })),
    })),
  };
}
/** Split cross-listed volume evenly so subject areas add up to school volume. */
export function subjectVolumes(courses: AcademicCourse[]) {
  const groups = new Map<
    string,
    { subject: string; count: number; courses: number }
  >();
  for (const c of courses) {
    const subjects = c.subjects.length ? c.subjects : ["OTHER"];
    for (const subject of subjects) {
      const row = groups.get(subject) ?? { subject, count: 0, courses: 0 };
      row.count += c.count / subjects.length;
      row.courses++;
      groups.set(subject, row);
    }
  }
  return [...groups.values()].sort(
    (a, b) => b.count - a.count || a.subject.localeCompare(b.subject),
  );
}

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
