import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, gradeRows } from "$lib/server/data";
export async function GET({ params, url, platform }) {
  const s = await assertRevision(url, platform);
  return apiJson(interactionSchemas.Grades, {
    ...(await gradeRows(params.uid, url, platform)),
    revision: s.revision,
  });
}
