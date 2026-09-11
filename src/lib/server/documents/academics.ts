import { query } from "$lib/server/data";
import { academicTerms } from "$lib/school-academics";
import { lectureSizes, type SchoolStats } from "$lib/school-stats";

export async function prepareAcademics(terms: SchoolStats["terms"]) {
  const [grades, courses, sections, teachers, courseCounts] = await Promise.all(
    [
      query(undefined, "SELECT * FROM grade_summaries"),
      query(
        undefined,
        "SELECT c.uid,c.code,c.title,(SELECT json_group_array(subject) FROM subjects s WHERE s.uid=c.uid) subjects FROM courses c",
      ),
      query(
        undefined,
        "SELECT term,uid,section,json_extract(payload,'$.total') total FROM grades WHERE section<>''",
      ),
      query(
        undefined,
        "SELECT term,COUNT(DISTINCT j.value) count FROM grades g,json_each(g.instructors) j WHERE json_extract(g.payload,'$.total')>0 GROUP BY term",
      ),
      query(
        undefined,
        "SELECT term,COUNT(DISTINCT uid) count FROM grades WHERE json_extract(payload,'$.total')>0 GROUP BY term",
      ),
    ],
  );
  const records = academicTerms(
    grades,
    courses.map((c) => ({ ...c, subjects: JSON.parse(c.subjects) })),
  );
  const counts = new Map<string, number[]>();
  const seen = new Set<string>();
  for (const row of sections) {
    const key = `${row.term}:${row.uid}:${row.section}`;
    if (seen.has(key) || !Number.isInteger(row.total) || row.total <= 0)
      continue;
    seen.add(key);
    const sizes = counts.get(row.term) ?? [];
    sizes.push(row.total);
    counts.set(row.term, sizes);
  }
  const recordedCounts = new Map(courseCounts.map((t) => [t.term, t.count]));
  const instructorCounts = new Map(teachers.map((t) => [t.term, t.count]));
  for (const [term, data] of Object.entries(terms)) {
    const sizes = lectureSizes(counts.get(term) ?? []);
    data.recordedInstructors = instructorCounts.get(term) ?? 0;
    data.recordedCourses = recordedCounts.get(term) ?? 0;
    data.gradedSections = sizes.knownLectures;
    data.gradedMedian = sizes.medianLecture;
    data.gradedSizes = sizes.sizes;
  }
  return records;
}
