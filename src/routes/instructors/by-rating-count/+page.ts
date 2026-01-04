import type { QuickStatistics } from "$lib/types/misc.ts";
import { createApiClient } from "$lib/api";
import { type FullInstructor, sanitizeInstructorId } from "$lib/types/instructor.ts";

export const load = async ({ fetch }) => {
  const api = createApiClient(fetch);

  const { data: quickStatistics, error: statsError } = await api.GET("/quick_statistics");
  if (statsError || !quickStatistics)
    throw new Error(`Failed to fetch quick statistics`);

  const instructorNames = (quickStatistics as QuickStatistics).most_rated_instructors;
  const instructors: FullInstructor[] = await Promise.all(
    instructorNames.map(async (name) => {
      const { data, error } = await api.GET("/instructors/{instructorId}", {
        params: { path: { instructorId: sanitizeInstructorId(name) } },
      });
      if (error || !data)
        throw new Error(`Failed to fetch instructor: ${name}`);
      return data;
    }),
  ); // Not efficient at all without server side caching, but this is a TODO i dont have time for this right now problem. womp womp

  return {
    subtitle: "Most Rated Instructors",
    instructors,
  };
};