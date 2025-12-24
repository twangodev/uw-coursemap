import type { Course } from "$lib/types/course.ts";
import { CourseUtils } from "$lib/types/course.ts";
import { calculateGradePointAverage, calculateARate } from "$lib/types/madgrades.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

/**
 * Generate a simple, informative meta description for a course
 */
export function generateCourseMetaDescription(course: Course): string {
  const latestTermKey = CourseUtils.getLatestTermKey(course);
  const enrollment = latestTermKey ? course.term_data[latestTermKey]?.enrollment_data : null;
  
  // Pre-calculate all values
  const base = course.description || `${CourseUtils.courseReferenceToString(course.course_reference)}: ${course.course_title}`;
  
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
  const courseCode = CourseUtils.courseReferenceToString(course.course_reference);
  return `${courseCode}: ${course.course_title} - UW-Madison`;
}

/**
 * Generate an Open Graph image URL for a course
 */
export function generateCourseOgImage(course: Course): string {
  const courseCode = CourseUtils.courseReferenceToString(course.course_reference);
  const latestTermKey = CourseUtils.getLatestTermKey(course);
  const enrollment = latestTermKey ? course.term_data[latestTermKey]?.enrollment_data : null;

  // Build description with credits, GPA, A-rate, and badges
  const descriptionParts: string[] = [];

  if (enrollment?.credit_count) {
    const credits = enrollment.credit_count[0] === enrollment.credit_count[1]
      ? `${enrollment.credit_count[0]} credits`
      : `${enrollment.credit_count[0]}-${enrollment.credit_count[1]} credits`;
    descriptionParts.push(credits);
  }

  if (course.cumulative_grade_data && course.cumulative_grade_data.total >= 50) {
    const gpa = calculateGradePointAverage(course.cumulative_grade_data);
    if (gpa !== null) {
      descriptionParts.push(`Avg GPA: ${gpa.toFixed(1)}`);
    }

    const aRate = calculateARate(course.cumulative_grade_data);
    if (aRate !== null) {
      descriptionParts.push(`${Math.round(aRate)}% A-rate`);
    }
  }

  // Add GenEd or Ethnic Studies badge
  if (enrollment?.general_education) {
    descriptionParts.push('GenEd');
  } else if (enrollment?.ethnic_studies) {
    descriptionParts.push('Ethnic Studies');
  }

  const description = descriptionParts.length > 0
    ? descriptionParts.join(' • ')
    : 'UW-Madison Course';

  return generateOgImageUrl({
    title: courseCode,
    subtitle: course.course_title,
    description: description,
  });
}