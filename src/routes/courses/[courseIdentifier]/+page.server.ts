import { redirect, error } from "@sveltejs/kit";
import { pageData, query } from "$lib/server/data";
import { gradeKeys, projectGrades } from "$lib/grade-projection";
import { instructorGradeTrends } from "$lib/server/instructor-trends";
import { courseContext } from "$lib/server/course-context";
import { normalize, courseUrl } from "$lib/format";
import entriesData from "../../../../.site/entries.json";
export const prerender = "auto";
export function entries() {
  return entriesData.courses.map((courseIdentifier) => ({ courseIdentifier }));
}
export async function load({ params, platform }) {
  if (!params.courseIdentifier.startsWith("course_")) {
    const matches = await query(
      platform,
      "SELECT uid FROM aliases WHERE alias=?",
      [normalize(params.courseIdentifier)],
    );
    if (matches.length === 1) redirect(308, courseUrl(matches[0].uid));
    if (matches.length > 1)
      redirect(307, "/search?q=" + encodeURIComponent(params.courseIdentifier));
    error(404, "Course not found");
  }
  const course = await pageData("courses", params.courseIdentifier, platform);
  const target = course.semester;
  const gradesReleased = course.grades.some(
    (row: any) =>
      row.term_id === target && gradeKeys.some((key) => Number(row[key]) > 0),
  );
  const [context, instructorTrends] = await Promise.all([courseContext(course, platform), instructorGradeTrends(course, platform)]);
  return {
    course,
    context,
    instructorTrends,
    projection:
      target && !gradesReleased ? projectGrades(course.grades, target) : null,
  };
}
