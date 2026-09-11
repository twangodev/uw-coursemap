import { error } from "@sveltejs/kit";
import type { SchoolStats } from "$lib/school-stats";
export function selectStatsTerm(stats: SchoolStats, url: URL): SchoolStats {
  const selectedTerm = url.searchParams.get("term") ?? stats.selectedTerm;
  if (!Object.hasOwn(stats.terms, selectedTerm))
    error(400, "Unknown statistics term");
  return { ...stats, selectedTerm };
}
