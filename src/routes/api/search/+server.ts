import { json } from "@sveltejs/kit";
import { assertRevision, search } from "$lib/server/data";
export async function GET({ url, platform }) {
  const s = await assertRevision(url, platform);
  return json(
    { ...(await search(url, platform)), revision: s.revision },
    { headers: { "Cache-Control": "public, max-age=60" } },
  );
}
