import type { DocumentContext } from "./types";
import { search as searchData } from "$lib/server/data";
export async function search({ url, platform }: DocumentContext) {
  return { results: await searchData(url, platform), discoveryFiltered: url.searchParams.size > 0 };
}
