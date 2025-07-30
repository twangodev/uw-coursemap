import type { FullInstructorInformation } from "$lib/types/instructor.ts";

/**
 * Generate a simple meta description for an instructor
 */
export function generateInstructorMetaDescription(instructor: FullInstructorInformation): string {
  // Pre-calculate all values
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