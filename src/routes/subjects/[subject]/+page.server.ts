import { error } from "@sveltejs/kit";
import { query } from "$lib/server/data";
import entriesData from "../../../../.site/entries.json";
export const prerender = true;
export function entries() {
  return entriesData.subjects.map((subject) => ({ subject }));
}
export async function load({ params, platform }) {
  const courses = await query(
    platform,
    "SELECT c.uid course_uid,c.code course_id,c.title,c.credits_min,c.credits_max,c.gpa FROM courses c JOIN subjects s ON s.uid=c.uid WHERE s.subject=? ORDER BY c.code",
    [params.subject],
  );
  if (!courses.length) error(404, "Department not found");
  return { subject: params.subject, courses };
}
