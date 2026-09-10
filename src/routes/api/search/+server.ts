import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, search } from "$lib/server/data";
export async function GET({ url, platform }) {
  const start = performance.now();
  const s = await assertRevision(url, platform);
  const results = await search(url, platform);
  return apiJson(
    interactionSchemas.Search,
    { ...results, revision: s.revision },
    {
      headers: {
        "Cache-Control": "public, max-age=60",
        "Server-Timing": `search;dur=${(performance.now() - start).toFixed(1)}`,
      },
    },
  );
}
