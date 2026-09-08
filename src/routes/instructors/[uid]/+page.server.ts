import { building } from "$app/environment";
import { instructorUrls } from "$lib/server/instructor-urls";
import { error, redirect } from "@sveltejs/kit";
import { pageData, query, status } from "$lib/server/data";
import { instructorReviews } from "$lib/server/reviews";
import { instructorCourses } from "$lib/server/instructor-courses";
export const prerender = "auto";
export async function entries() {
  return [...(await instructorUrls()).values()].map((url) => ({
    uid: decodeURIComponent(url.split("/").at(-1)!),
  }));
}
export async function load({ params, platform, setHeaders, url }) {
  const urls = await instructorUrls(platform);
  const path = "/instructors/" + encodeURIComponent(params.uid);
  let uid = [...urls].find(([, value]) => value === path)?.[0];
  if (!uid && urls.has(params.uid))
    redirect(308, urls.get(params.uid)! + (building ? "" : url.search));
  if (!uid) error(404, "Instructor not found");
  const instructor = await pageData("instructors", uid, platform);
  const history = await query(
    platform,
    "SELECT t.term,c.uid course_uid,c.code course_id,c.title FROM teaching t JOIN courses c ON c.uid=t.course_uid WHERE t.instructor_uid=? ORDER BY t.term DESC,c.code LIMIT 100",
    [uid],
  );
  setHeaders({ "Cache-Control": "public, max-age=0, s-maxage=3600" });
  const timeline = await query(
    platform,
    "SELECT term,count(DISTINCT course_uid) courses FROM teaching WHERE instructor_uid=? GROUP BY term ORDER BY term",
    [uid],
  );
  const dataset = await status(platform);
  const term = dataset.term;
  const [courses, reviews] = await Promise.all([
    instructorCourses(uid, term, platform),
    instructorReviews(uid, 1, "", platform),
  ]);
  return { instructor, history, timeline, term, courses, reviews };
}
