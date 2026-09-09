import { search } from "$lib/server/data";
export async function load({ url, platform }) {
  return { results: await search(url, platform), discoveryFiltered: url.searchParams.size > 0 };
}
