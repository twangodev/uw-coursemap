import { type Course, CourseUtils } from "$lib/types/course.ts";
import { getLatestTermId, type Terms } from "$lib/types/terms.ts";
import { apiFetch } from "$lib/api.ts";
import type { GradeData } from "$lib/types/madgrades.ts";
import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import anyAscii from "any-ascii";

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

export type MandatoryAttendance = {
  neither: number;
  no: number;
  total: number;
  yes: number;
};

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
 * "total" is skipped since it's presumably an aggregate.
 */
export function getAttendanceRequirement(
  data: MandatoryAttendance | undefined,
): AttendanceRequirement {
  if (!data) {
    return {
      most: "Unknown",
      count: 0,
      total: 0,
    };
  }

  const relevantKeys = ["neither", "no", "yes"] as const;

  // Identify the key among neither/no/yes that has the highest value.
  const largestKey = relevantKeys.reduce((acc, key) => {
    return data[key] > data[acc] ? key : acc;
  }, "neither");

  // Build and return the result object
  return {
    most: attendanceLabels[largestKey],
    count: data[largestKey],
    total: data.total,
  };
}

type Ratings = {
  comment: string;
  difficulty_rating: number;
  quality_rating: number;
};

export type RatingsDistribution = {
  r1: number;
  r2: number;
  r3: number;
  r4: number;
  r5: number;
  total: number;
};

export type Instructor = {
  average_difficulty: number;
  average_rating: number;
  id: string;
  legacy_id: string;
  mandatory_attendance: MandatoryAttendance;
  num_ratings: number;
  ratings: Ratings[];
  ratings_distribution: RatingsDistribution;
  would_take_again_percent: number;
};

export type FullInstructorInformation = {
  name: string;
  email: string;
  credentials: string | null;
  department: string | null;
  official_name: string | null;
  position: string | null;
  rmp_data: Instructor | null;
  courses_taught: string[];
  cumulative_grade_data: GradeData | null;
};

export async function getFullInstructorInformation(
  course: Course,
  terms: Terms,
  selectedTerm: string | undefined,
  fetch: (url: string) => Promise<Response>,
): Promise<FullInstructorInformation[]> {
  let rawInstructors = [];
  for (const [name, email] of Object.entries(
    CourseUtils.getInstructorsWithEmail(course, selectedTerm ?? getLatestTermId(terms)),
  )) {
    const response = await fetch(
      `${env.PUBLIC_API_URL}/instructors/${sanitizeInstructorId(name)}.json`,
    );
    if (!response.ok) {
      console.error(
        `Failed to fetch instructor data for ${name}: ${response.statusText}`,
      );
      continue;
    }
    const data: FullInstructorInformation =
      response.status === 200
        ? await response.json()
        : {
            name,
            email: email ?? null,
            credentials: null,
            department: null,
            official_name: null,
            position: null,
            rmp_data: null,
          };
    rawInstructors.push(data);
  }

  return rawInstructors.toSorted((a, b) => {
    if (!a.rmp_data?.average_rating) return 1;
    if (!b.rmp_data?.average_rating) return -1;
    return b.rmp_data.average_rating - a.rmp_data.average_rating;
  });
}
