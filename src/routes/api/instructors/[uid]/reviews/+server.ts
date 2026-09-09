import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, pageNumber } from "$lib/server/data";
import { instructorReviews } from "$lib/server/reviews";
export async function GET({ params, url, platform }) {
  const status = await assertRevision(url, platform);
  return apiJson(interactionSchemas.InstructorReviews, {
    ...(await instructorReviews(
      params.uid,
      pageNumber(url),
      url.searchParams.get("course") || "",
      platform,
    )),
    revision: status.revision,
  });
}
