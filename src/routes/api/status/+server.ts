import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { status } from "$lib/server/data";
export async function GET({ platform }) {
  return apiJson(interactionSchemas.Status, await status(platform), {
    headers: { "Cache-Control": "no-store" },
  });
}
