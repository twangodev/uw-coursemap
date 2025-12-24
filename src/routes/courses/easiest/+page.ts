import { env } from "$env/dynamic/public";
import type { QuickStatistics } from "$lib/types/misc.ts";
import {
  type Course,
  CourseUtils,
} from "$lib/types/course.ts";

const { PUBLIC_API_URL } = env;

export const load = async ({ fetch }) => {
  const quickStatisticsResponse = await fetch(
    `${PUBLIC_API_URL}/quick_statistics.json`,
  );
  if (!quickStatisticsResponse.ok)
    throw new Error(
      `Failed to fetch quick statistics: ${quickStatisticsResponse.statusText}`,
    );
  const quickStatistics: QuickStatistics = await quickStatisticsResponse.json();

  const courseReferences = quickStatistics.top_100_a_rate_chances.map(
    (item) => item.reference,
  );
  const courses: Course[] = await Promise.all(
    courseReferences.map(async (reference) => {
      const sanitized = CourseUtils.courseReferenceToSanitizedString(reference);
      const response = await fetch(
        `${PUBLIC_API_URL}/course/${sanitized}.json`,
      );
      if (!response.ok)
        throw new Error(`Failed to fetch course: ${response.statusText}`);
      return await response.json();
    }),
  ); // Not efficient at all without server side caching, but this is a TODO i dont have time for this right now problem. womp womp

  return {
    subtitle: "Easiest Courses",
    courses: courses,
  };
};
