import type { Course } from '$lib/types/course.ts';
import type { FullInstructorInformation } from '$lib/types/instructor.ts';
import { CourseDescriptionBuilder } from './builder.ts';
import type { GenerationOptions, DescriptionType } from './types.ts';
import { courseReferenceToString } from '$lib/types/course.ts';

/**
 * Generate an enhanced course description optimized for SEO
 * 
 * @param course - The course data
 * @param instructors - Array of instructor information
 * @param options - Optional generation options (type, variant, config)
 * @returns SEO-optimized description string
 * 
 * @example
 * // Generate default description
 * const description = generateEnhancedCourseDescription(course, instructors);
 * 
 * @example
 * // Generate meta description (160 chars)
 * const metaDesc = generateEnhancedCourseDescription(course, instructors, { variant: 'meta' });
 * 
 * @example
 * // Generate social media description
 * const socialDesc = generateEnhancedCourseDescription(course, instructors, { variant: 'social' });
 */
export function generateEnhancedCourseDescription(
  course: Course,
  instructors: FullInstructorInformation[],
  options?: GenerationOptions
): string {
  const builder = new CourseDescriptionBuilder(course, instructors, options);
  return builder.build();
}

/**
 * Generate course keywords for SEO
 * 
 * @param course - The course data
 * @param instructors - Array of instructor information  
 * @returns Array of relevant keywords
 */
export function generateCourseKeywords(
  course: Course,
  instructors: FullInstructorInformation[]
): string[] {
  const keywords: Set<string> = new Set();
  
  // Course identifiers
  const courseCode = courseReferenceToString(course.course_reference);
  keywords.add(courseCode.toLowerCase());
  
  // Add variations
  course.course_reference.subjects.forEach(subject => {
    keywords.add(subject.toLowerCase());
    keywords.add(`${subject} ${course.course_reference.course_number}`.toLowerCase());
    keywords.add(`${subject}${course.course_reference.course_number}`.toLowerCase());
  });
  
  // Title words (excluding common words)
  const commonWords = new Set(['the', 'and', 'or', 'in', 'of', 'to', 'for', 'with', 'a', 'an']);
  const titleWords = course.course_title.toLowerCase().split(/\s+/)
    .filter(word => word.length > 3 && !commonWords.has(word));
  titleWords.forEach(word => keywords.add(word));
  
  // Level
  const courseNumber = course.course_reference.course_number;
  if (courseNumber < 300) {
    keywords.add('introductory');
    keywords.add('intro');
    keywords.add('beginner');
  } else if (courseNumber < 500) {
    keywords.add('intermediate');
  } else if (courseNumber < 700) {
    keywords.add('advanced');
    keywords.add('upper-level');
  } else {
    keywords.add('graduate');
    keywords.add('grad');
  }
  
  // Attributes
  const latestTermKey = Object.keys(course.term_data).sort().reverse()[0];
  if (latestTermKey) {
    const enrollment = course.term_data[latestTermKey]?.enrollment_data;
    if (enrollment?.general_education) {
      keywords.add('general education');
      keywords.add('gen ed');
    }
    if (enrollment?.ethnic_studies) {
      keywords.add('ethnic studies');
      keywords.add('diversity');
    }
  }
  
  // Top instructors
  instructors
    .filter(i => i.rmp_data && i.rmp_data.average_rating > 3.5)
    .slice(0, 2)
    .forEach(i => keywords.add(i.name.toLowerCase()));
  
  // University keywords
  keywords.add('uw madison');
  keywords.add('uw-madison');
  keywords.add('university of wisconsin');
  keywords.add('wisconsin');
  keywords.add('madison');
  
  return Array.from(keywords);
}

/**
 * Generate a structured title for the course page
 * 
 * @param course - The course data
 * @returns SEO-optimized title string
 */
export function generateStructuredCourseTitle(course: Course): string {
  const courseCode = courseReferenceToString(course.course_reference);
  return `${courseCode}: ${course.course_title} - UW-Madison`;
}

// Re-export types for convenience
export type { GenerationOptions, DescriptionType } from './types.ts';
export { descriptionVariants } from './config.ts';