import { json } from "@sveltejs/kit";
import { assertRevision, pageNumber } from "$lib/server/data";
import { instructorReviews } from "$lib/server/reviews";
export async function GET({ params, url, platform }) {
  const status = await assertRevision(url, platform);
  return json({
    ...(await instructorReviews(
      params.uid,
      pageNumber(url),
      url.searchParams.get("course") || "",
      platform,
    )),
    revision: status.revision,
  });
}
