import { createApiClient } from "$lib/api";
import type { QuickStatistics } from "$lib/types/misc.ts";
import {
  type Course,
  CourseUtils,
} from "$lib/types/course.ts";

export const load = async ({ fetch }) => {
  const api = createApiClient(fetch);

  const { data: quickStatistics, error: statsError } = await api.GET("/quick_statistics");
  if (statsError || !quickStatistics)
    throw new Error(`Failed to fetch quick statistics`);

  const courseReferences = (quickStatistics as QuickStatistics).top_100_a_rate_chances.map(
    (item) => item.reference,
  );
  const courses: Course[] = await Promise.all(
    courseReferences.map(async (reference) => {
      const sanitized = CourseUtils.courseReferenceToSanitizedString(reference);
      const { data, error } = await api.GET("/course/{courseId}", {
        params: { path: { courseId: sanitized } },
      });
      if (error || !data)
        throw new Error(`Failed to fetch course: ${sanitized}`);
      return data;
    }),
  ); // Not efficient at all without server side caching, but this is a TODO i dont have time for this right now problem. womp womp

  return {
    subtitle: "Easiest Courses",
    courses,
  };
};
