import { building } from "$app/environment";
import { error } from "@sveltejs/kit";
// Keep the initial page static; URL filters fetch a revision-pinned search projection.
export async function load({ data, url, fetch, parent }) {
  if (building || !url.search) return data;
  const { status } = await parent();
  const query = new URLSearchParams(url.searchParams);
  query.set("subject", data.subject);
  query.set("kind", "course");
  query.set("revision", status.revision);
  const response = await fetch(`/api/search?${query}`);
  if (!response.ok)
    error(
      response.status,
      "Courses could not be loaded. Reload to check for an updated dataset.",
    );
  return { ...data, results: (await response.json()) as typeof data.results };
}
