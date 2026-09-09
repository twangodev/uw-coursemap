import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, search } from "$lib/server/data";
export async function GET({ url, platform }) {
  const s = await assertRevision(url, platform);
  return apiJson(
    interactionSchemas.Search,
    { ...(await search(url, platform)), revision: s.revision },
    { headers: { "Cache-Control": "public, max-age=60" } },
  );
}
