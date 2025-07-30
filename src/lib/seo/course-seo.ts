import type { Course } from "$lib/types/course.ts";
import { courseReferenceToString } from "$lib/types/course.ts";
import { calculateGradePointAverage } from "$lib/types/madgrades.ts";

/**
 * Generate a simple, informative meta description for a course
 */
export function generateCourseMetaDescription(course: Course): string {
  const latestTermKey = Object.keys(course.term_data).sort().reverse()[0];
  const enrollment = course.term_data[latestTermKey]?.enrollment_data;
  
  // Pre-calculate all values
  const base = course.description || `${courseReferenceToString(course.course_reference)}: ${course.course_title}`;
  
  const credits = enrollment?.credit_count
    ? enrollment.credit_count[0] === enrollment.credit_count[1]
      ? `${enrollment.credit_count[0]} credits`
      : `${enrollment.credit_count[0]}-${enrollment.credit_count[1]} credits`
    : '';
  
  const gpa = course.cumulative_grade_data && course.cumulative_grade_data.total >= 50
    ? calculateGradePointAverage(course.cumulative_grade_data)
    : null;
  
  // Single template string assembly
  return `${base} ${credits ? `${credits}` : ''}${gpa ? `. Average GPA: ${gpa.toFixed(1)}` : ''}`;
}


/**
 * Generate a structured title for the course page
 */
export function generateCourseTitle(course: Course): string {
  const courseCode = courseReferenceToString(course.course_reference);
  return `${courseCode}: ${course.course_title} - UW-Madison`;
}