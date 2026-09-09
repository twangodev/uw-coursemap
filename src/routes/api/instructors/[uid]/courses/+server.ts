import { apiJson } from "$lib/server/api-response";
import { interactionSchemas } from "$lib/api/schemas";
import { assertRevision, pageData } from "$lib/server/data";
import { instructorCourses } from "$lib/server/instructor-courses";
export async function GET({ params, url, platform }) {
  const status = await assertRevision(url, platform);
  await pageData("instructors", params.uid, platform);
  const term = url.searchParams.get("term") || status.term;
  return apiJson(interactionSchemas.InstructorCourses, {
    courses: await instructorCourses(params.uid, term, platform),
    term,
    revision: status.revision,
  });
}
