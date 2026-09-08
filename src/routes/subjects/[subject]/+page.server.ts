import { error } from "@sveltejs/kit";
import { query, search } from "$lib/server/data";
import { departmentStats } from "$lib/server/departments";
import entriesData from "../../../../.site/entries.json";
export const prerender = "auto";
export function entries() {
  return entriesData.subjects.map((subject) => ({ subject }));
}
export async function load({ params, platform }) {
  if (
    !(
      await query(
        platform,
        "SELECT uid FROM subjects WHERE subject=? LIMIT 1",
        [params.subject],
      )
    ).length
  )
    error(404, "Department not found");
  const searchUrl = new URL("http://prerender/search");
  searchUrl.searchParams.set("subject", params.subject);
  searchUrl.searchParams.set("kind", "course");
  const [results, stats] = await Promise.all([
    search(searchUrl, platform),
    departmentStats(params.subject, platform),
  ]);
  return { subject: params.subject, results, stats };
}
