import { json } from "@sveltejs/kit";
import { assertRevision, pageData } from "$lib/server/data";
import { instructorCourses } from "$lib/server/instructor-courses";
export async function GET({ params, url, platform }) {
  const status = await assertRevision(url, platform);
  await pageData("instructors", params.uid, platform);
  const term = url.searchParams.get("term") || status.term;
  return json({
    courses: await instructorCourses(params.uid, term, platform),
    term,
    revision: status.revision,
  });
}
