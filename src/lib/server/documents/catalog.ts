import type { DocumentContext } from "./types";
import { error, redirect } from "@sveltejs/kit";
import { query } from "$lib/server/data";
export async function catalog({ params, platform }: DocumentContext) {
  if (params.subject !== params.subject.toUpperCase())
    redirect(
      308,
      `/departments/${encodeURIComponent(params.subject.toUpperCase())}/catalog`,
    );
  const catalog = await query(
    platform,
    "SELECT c.code course_id,c.title,c.description,c.credits_min,c.credits_max FROM courses c JOIN subjects s ON s.uid=c.uid WHERE s.subject=? ORDER BY c.code",
    [params.subject],
  );
  if (!catalog.length) error(404, "Department not found");
  return { subject: params.subject, catalog };
}
