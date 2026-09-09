import { building } from "$app/environment";
import { redirect, error } from "@sveltejs/kit";
import { pageData, query } from "$lib/server/data";
import { gradeKeys, projectGrades } from "$lib/grade-projection";
import { instructorGradeTrends } from "$lib/server/instructor-trends";
import { courseFollowers } from "$lib/server/course-map";
import { courseContext } from "$lib/server/course-context";
import { normalize, courseUrl, courseSlug } from "$lib/format";
export const prerender = "auto";
export async function entries() {
  const courses = await query(undefined, "SELECT code FROM courses");
  const slugs = courses.map((course) => courseSlug(course.code));
  if (new Set(slugs).size !== slugs.length)
    throw new Error(
      "Course URL collision: readable URLs must identify a unique course.",
    );
  return slugs.map((courseIdentifier) => ({ courseIdentifier }));
}
export async function load({ params, platform, url }) {
  let uid = params.courseIdentifier;
  if (uid.startsWith("course_")) error(404, "Course not found");
  const matches = await query(
    platform,
    "SELECT c.uid,c.code FROM aliases a JOIN courses c ON c.uid=a.uid WHERE a.alias=?",
    [normalize(uid)],
  );
  // A current canonical code wins over a reused historical alias.
  const currentMatches = matches.filter(
    (course) => courseSlug(course.code).toLowerCase() === uid.toLowerCase(),
  );
  if (currentMatches.length === 1) uid = currentMatches[0].uid;
  else if (matches.length === 1) uid = matches[0].uid;
  else if (matches.length > 1)
    redirect(307, "/search?q=" + encodeURIComponent(params.courseIdentifier));
  else error(404, "Course not found");

  const course = await pageData("courses", uid, platform);
  const canonical = courseUrl(course.course_id);
  if (params.courseIdentifier !== courseSlug(course.course_id))
    redirect(308, canonical + (building ? "" : url.search));
  const target = course.semester;
  const gradesReleased = course.grades.some(
    (row: any) =>
      row.term_id === target && gradeKeys.some((key) => Number(row[key]) > 0),
  );
  const [context, instructorTrends, following] = await Promise.all([
    courseContext(course, platform),
    instructorGradeTrends(course, platform),
    courseFollowers(uid, platform),
  ]);
  return {
    course,
    context,
    instructorTrends,
    following,
    projection:
      target && !gradesReleased ? projectGrades(course.grades, target) : null,
  };
}
