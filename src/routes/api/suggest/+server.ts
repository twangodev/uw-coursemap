import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, search } from "$lib/server/data";

export async function GET({ url, platform }) {
  const start = performance.now();
  const status = await assertRevision(url, platform);
  const { items } = await search(url, platform, true);
  return apiJson(
    interactionSchemas.Suggestions,
    { items, revision: status.revision },
    {
      headers: {
        "Cache-Control": "public, max-age=60",
        "Server-Timing": `suggest;dur=${(performance.now() - start).toFixed(1)}`,
      },
    },
  );
}
