import type { DocumentContext } from "./types";
import { search } from "$lib/server/data";
export async function instructors({ url, platform }: DocumentContext) {
  const selected = new URL(url);
  selected.searchParams.set("kind", "instructor");
  return { results: await search(selected, platform), discoveryFiltered: url.searchParams.size > 0 };
}
