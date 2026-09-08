import { building } from "$app/environment";
import { error } from "@sveltejs/kit";
export async function load({ data, url, fetch, parent }) {
  if (building || !url.search) return data;
  const { status } = await parent();
  const query = new URLSearchParams(url.searchParams);
  query.set("kind", "course");
  query.set("ranking", data.collection);
  query.set("revision", status.revision);
  const response = await fetch(`/api/search?${query}`);
  if (!response.ok)
    error(
      response.status,
      "Courses could not be loaded. Try reloading the page.",
    );
  return { ...data, results: (await response.json()) as typeof data.results };
}
