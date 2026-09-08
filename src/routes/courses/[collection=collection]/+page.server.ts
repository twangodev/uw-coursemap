import { search } from "$lib/server/data";
import {
  courseCollections,
  type CourseCollection,
} from "$lib/course-collections";
export const prerender = "auto";
export const entries = () =>
  (Object.keys(courseCollections) as CourseCollection[]).map((collection) => ({
    collection,
  }));
export async function load({ params, platform }) {
  const url = new URL("http://prerender/search");
  url.searchParams.set("ranking", params.collection);
  return {
    collection: params.collection,
    subject: "",
    results: await search(url, platform),
  };
}
