import { building } from "$app/environment";
import { error } from "@sveltejs/kit";
export async function load({ data, url, fetch, parent }) {
  if (building || !url.searchParams.has("term")) return data;
  const { status } = await parent();
  const query = new URLSearchParams({
    term: url.searchParams.get("term") || status.term,
    revision: status.revision,
  });
  const response = await fetch(
    `/api/instructors/${data.instructor.instructor_uid}/courses?${query}`,
  );
  if (!response.ok)
    error(
      response.status,
      "Teaching records could not be loaded. Reload to check for an updated dataset.",
    );
  const selected = (await response.json()) as {
    term: string;
    courses: typeof data.courses;
  };
  return { ...data, ...selected };
}
