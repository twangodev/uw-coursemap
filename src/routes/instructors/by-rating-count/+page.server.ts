import { search } from "$lib/server/data";
export async function load({ url, platform }) {
  const selected = new URL(url);
  selected.searchParams.set("kind", "instructor");
  return { results: await search(selected, platform) };
}
