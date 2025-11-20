import type { FullInstructorInformation } from "$lib/types/instructor.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

/**
 * Generate a simple meta description for an instructor
 */
export function generateInstructorMetaDescription(instructor: FullInstructorInformation): string {
  // If AI-generated summary exists, use it for better SEO
  if (instructor.summary) {
    return instructor.summary;
  }

  // Fallback to existing stats-based description
  const position = instructor.position || "faculty member";
  const department = instructor.department || "UW-Madison";

  // RMP data
  const rating = instructor.rmp_data?.average_rating?.toFixed(1);
  const numRatings = instructor.rmp_data?.num_ratings;
  const wouldTakeAgain = instructor.rmp_data?.would_take_again_percent;

  // Courses taught
  const courseCount = instructor.courses_taught?.length || 0;

  // Build base description
  const base = `${instructor.name} is a ${position} in ${department} at UW-Madison`;

  // Add rating info
  const ratingInfo = rating && numRatings
    ? `. ${rating}/5.0 rating from ${numRatings} students`
    : '';

  // Add would take again if high
  const takeAgainInfo = wouldTakeAgain && wouldTakeAgain > 80
    ? `. ${Math.round(wouldTakeAgain)}% would take again`
    : '';

  // Add courses if many
  const coursesInfo = courseCount > 5
    ? `. Teaches ${courseCount} courses`
    : '';

  // Single template string assembly
  return `${base}${ratingInfo}${takeAgainInfo}${coursesInfo}`;
}

/**
 * Generate a structured title for the instructor page
 */
export function generateInstructorTitle(instructor: FullInstructorInformation): string {
  return `${instructor.name} - ${instructor.department || "UW-Madison"}`;
}

/**
 * Generate an Open Graph image URL for an instructor
 */
export function generateInstructorOgImage(instructor: FullInstructorInformation): string {
  const position = instructor.position || "Faculty";
  const department = instructor.department || "UW-Madison";

  // Build description with rating, would take again %, and courses
  const descriptionParts: string[] = [];

  const rating = instructor.rmp_data?.average_rating;
  const numRatings = instructor.rmp_data?.num_ratings;
  const wouldTakeAgain = instructor.rmp_data?.would_take_again_percent;

  if (rating && numRatings) {
    descriptionParts.push(`${rating.toFixed(1)}/5.0 from ${numRatings} reviews`);
  }

  if (wouldTakeAgain !== undefined && wouldTakeAgain > 0) {
    descriptionParts.push(`${Math.round(wouldTakeAgain)}% would take again`);
  }

  const courseCount = instructor.courses_taught?.length || 0;
  if (courseCount > 0) {
    descriptionParts.push(`${courseCount} courses taught`);
  }

  const description = descriptionParts.length > 0
    ? descriptionParts.join(' • ')
    : 'UW-Madison Faculty';

  return generateOgImageUrl({
    title: instructor.name,
    subtitle: `${position}, ${department}`,
    description: description,
  });
}