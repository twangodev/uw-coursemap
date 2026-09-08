import { error } from "@sveltejs/kit";
import { search, query } from "$lib/server/data";
import {
  courseCollections,
  type CourseCollection,
} from "$lib/course-collections";
import entriesData from "../../../../../.site/entries.json";
export const prerender = "auto";
export const entries = () =>
  entriesData.subjects.flatMap((subject) =>
    (Object.keys(courseCollections) as CourseCollection[]).map(
      (collection) => ({ subject, collection }),
    ),
  );
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
  const url = new URL("http://prerender/search");
  url.searchParams.set("ranking", params.collection);
  url.searchParams.set("subject", params.subject);
  return {
    subject: params.subject,
    collection: params.collection,
    results: await search(url, platform),
  };
}
