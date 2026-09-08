import { building } from "$app/environment";
import { error } from "@sveltejs/kit";
import type { Status } from "$lib/types";
export async function loadCollection({
  data,
  url,
  fetch,
  parent,
}: {
  data: { collection: string; subject: string; results: any };
  url: URL;
  fetch: typeof globalThis.fetch;
  parent: () => Promise<{ status: Status }>;
}) {
  if (building || !url.search) return data;
  const { status } = await parent();
  const query = new URLSearchParams(url.searchParams);
  query.set("kind", "course");
  if (data.subject) query.set("subject", data.subject);
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
