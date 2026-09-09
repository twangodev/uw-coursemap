import { error } from "@sveltejs/kit";
import { query } from "./data";
import { coursePreviews } from "./discovery";
export async function instructorCourses(
  uid: string,
  term: string,
  platform?: App.Platform,
) {
  if (!/^1\d{2}[246]$/.test(term)) error(400, "Invalid term");
  const taught = await query(
    platform,
    "SELECT DISTINCT c.uid course_uid,c.code course_id,c.title,c.credits_min,c.credits_max,c.gpa FROM teaching t JOIN courses c ON c.uid=t.course_uid WHERE t.instructor_uid=? AND t.term=? ORDER BY c.code",
    [uid, term],
  );
  return coursePreviews(taught, term, platform, uid);
}
