import { query } from "./data";
import { instructorSeries } from "$lib/instructor-trends";

export async function instructorGradeTrends(course: any, platform?: App.Platform) {
  // Canonical section rows are unique by course/term/section. Shared sections
  // contribute once to each listed instructor, never to a summed course average.
  const rows = await query<Record<string, any>>(platform, `
    SELECT instructor.value AS instructor_uid, g.term, COUNT(*) AS sections,
      ${["a", "ab", "b", "bc", "c", "d", "f"].map((key) => `SUM(COALESCE(json_extract(g.payload, '$.${key}'), 0)) AS ${key}`).join(",")}
    FROM grades g, json_each(g.instructors) instructor
    WHERE g.uid=? AND g.section<>''
    GROUP BY instructor.value, g.term ORDER BY g.term
  `, [course.course_uid]);
  return instructorSeries(rows, new Map((course.grade_instructors || course.instructors).map((instructor: any) => [instructor.instructor_uid, instructor.name])));
}
