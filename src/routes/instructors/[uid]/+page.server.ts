import { redirect } from "@sveltejs/kit";
import { pageData, query } from "$lib/server/data";
import entriesData from "../../../../.site/entries.json";
export const prerender = "auto";
export function entries() {
  return entriesData.instructors.map((uid) => ({ uid }));
}
export async function load({ params, platform, setHeaders }) {
  if (!params.uid.startsWith("instructor_"))
    redirect(
      307,
      "/search?kind=instructor&q=" + encodeURIComponent(params.uid),
    );
  const instructor = await pageData("instructors", params.uid, platform);
  const history = await query(
    platform,
    "SELECT t.term,c.uid course_uid,c.code course_id,c.title FROM teaching t JOIN courses c ON c.uid=t.course_uid WHERE t.instructor_uid=? ORDER BY t.term DESC,c.code LIMIT 100",
    [params.uid],
  );
  setHeaders({ "Cache-Control": "public, max-age=0, s-maxage=3600" });
  const timeline = await query(
    platform,
    "SELECT term,count(DISTINCT course_uid) courses FROM teaching WHERE instructor_uid=? GROUP BY term ORDER BY term",
    [params.uid],
  );
  return { instructor, history, timeline };
}
