import { json } from "@sveltejs/kit";
import { assertRevision, query, pageNumber } from "$lib/server/data";
export async function GET({ params, url, platform }) {
  const s = await assertRevision(url, platform);
  const page = pageNumber(url);
  const items = await query(
    platform,
    "SELECT t.term,c.uid course_uid,c.code course_id,c.title FROM teaching t JOIN courses c ON c.uid=t.course_uid WHERE t.instructor_uid=? ORDER BY t.term DESC,c.code LIMIT 100 OFFSET ?",
    [params.uid, (page - 1) * 100],
  );
  return json({ items, page, revision: s.revision });
}
