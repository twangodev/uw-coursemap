import type { components } from "$lib/types/api";
import { type Course, CourseUtils } from "$lib/types/course.ts";
import { getLatestTermId, type Terms } from "$lib/types/terms.ts";
import { createApiClient } from "$lib/api";
import anyAscii from "any-ascii";

// Re-export types from generated API
export type FullInstructor = components["schemas"]["FullInstructor"];
export type RMPData = components["schemas"]["RMPData"];
export type MandatoryAttendance = components["schemas"]["MandatoryAttendance"];
export type RatingsDistribution = components["schemas"]["RatingsDistribution"];

/** Convert instructor name to uppercase URL-safe ID. e.g., "O'Brien Jr." → "OBRIEN_JR" */
export function sanitizeInstructorId(name: string): string {
  return anyAscii(name)
    .replaceAll(" ", "_")
    .replaceAll("/", "_")
    .replaceAll("'", "")
    .replaceAll(".", "")
    .toUpperCase()
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}

const attendanceLabels: Record<
  keyof Omit<MandatoryAttendance, "total">,
  string
> = {
  neither: "Unknown",
  no: "Optional",
  yes: "Required",
};

export type AttendanceRequirement = {
  most: string;
  count: number;
  total: number;
};

/**
 * Returns the attendance requirement with the highest count.
 */
export function getAttendanceRequirement(
  data: MandatoryAttendance | undefined | null,
): AttendanceRequirement {
  if (!data) {
    return {
      most: "Unknown",
      count: 0,
      total: 0,
    };
  }

  const relevantKeys = ["neither", "no", "yes"] as const;

  const largestKey = relevantKeys.reduce((acc, key) => {
    return data[key] > data[acc] ? key : acc;
  }, "neither" as const);

  return {
    most: attendanceLabels[largestKey],
    count: data[largestKey],
    total: data.total,
  };
}

export async function getFullInstructor(
  course: Course,
  terms: Terms,
  selectedTerm: string | undefined,
  fetchFn: typeof fetch,
): Promise<FullInstructor[]> {
  const api = createApiClient(fetchFn);
  let rawInstructors: FullInstructor[] = [];

  for (const [name, email] of Object.entries(
    CourseUtils.getInstructorsWithEmail(course, selectedTerm ?? getLatestTermId(terms)),
  )) {
    const { data, error } = await api.GET("/instructors/{instructorId}", {
      params: { path: { instructorId: sanitizeInstructorId(name) } },
    });

    if (error || !data) {
      console.error(`Failed to fetch instructor data for ${name}`);
      continue;
    }

    rawInstructors.push(data);
  }

  return rawInstructors.toSorted((a, b) => {
    if (!a.rmp_data?.average_rating) return 1;
    if (!b.rmp_data?.average_rating) return -1;
    return b.rmp_data.average_rating - a.rmp_data.average_rating;
  });
}