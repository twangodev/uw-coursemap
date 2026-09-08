import { json } from "@sveltejs/kit";
import { assertRevision, gradeRows } from "$lib/server/data";
export async function GET({ params, url, platform }) {
  const s = await assertRevision(url, platform);
  return json({
    ...(await gradeRows(params.uid, url, platform)),
    revision: s.revision,
  });
}
