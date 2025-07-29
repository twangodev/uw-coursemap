import type { Course } from "$lib/types/course.ts";
import type { FullInstructorInformation } from "$lib/types/instructor.ts";
import { courseReferenceToString } from "$lib/types/course.ts";
import { calculateGradePointAverage, calculateCompletionRate, calculateARate } from "$lib/types/madgrades.ts";

export function generateEnhancedCourseDescription(
  course: Course,
  instructors: FullInstructorInformation[]
): string {
  const baseDescription = course.description || "";
  const courseCode = courseReferenceToString(course.course_reference);
  
  const parts: string[] = [baseDescription];
  
  // Add credit information
  const latestTerm = Object.keys(course.term_data).sort().reverse()[0];
  if (latestTerm && course.term_data[latestTerm]?.enrollment_data?.credit_count) {
    const [minCredits, maxCredits] = course.term_data[latestTerm].enrollment_data.credit_count;
    if (minCredits === maxCredits) {
      parts.push(`This ${minCredits}-credit course`);
    } else {
      parts.push(`This ${minCredits}-${maxCredits} credit course`);
    }
  }
  
  // Add prerequisites
  if (course.prerequisites?.prerequisites_text && course.prerequisites.prerequisites_text !== "None") {
    parts.push(`Prerequisites: ${course.prerequisites.prerequisites_text}.`);
  }
  
  // Add when typically offered
  if (latestTerm && course.term_data[latestTerm]?.enrollment_data?.typically_offered) {
    const typicallyOffered = course.term_data[latestTerm].enrollment_data.typically_offered;
    parts.push(`Typically offered in ${typicallyOffered}.`);
  }
  
  // Add grade statistics
  if (course.cumulative_grade_data && course.cumulative_grade_data.total > 50) {
    const gpa = calculateGradePointAverage(course.cumulative_grade_data);
    const completionRate = calculateCompletionRate(course.cumulative_grade_data);
    const aRate = calculateARate(course.cumulative_grade_data);
    
    if (gpa !== null) {
      parts.push(`Historical average GPA: ${gpa.toFixed(2)}/4.0.`);
    }
    if (completionRate !== null) {
      parts.push(`${(completionRate * 100).toFixed(0)}% completion rate.`);
    }
    if (aRate !== null && aRate > 0.3) {
      parts.push(`${(aRate * 100).toFixed(0)}% of students receive an A or AB.`);
    }
  }
  
  // Add instructor information
  if (instructors.length > 0) {
    const topInstructors = instructors
      .filter(i => i.rmp_data && i.rmp_data.average_rating > 3.5)
      .slice(0, 3)
      .map(i => i.name);
    
    if (topInstructors.length > 0) {
      parts.push(`Taught by highly-rated instructors including ${topInstructors.join(", ")}.`);
    }
  }
  
  // Add attributes
  const attributes: string[] = [];
  if (latestTerm && course.term_data[latestTerm]?.enrollment_data?.general_education) {
    attributes.push("General Education");
  }
  if (latestTerm && course.term_data[latestTerm]?.enrollment_data?.ethnic_studies) {
    attributes.push("Ethnic Studies");
  }
  if (attributes.length > 0) {
    parts.push(`This course fulfills ${attributes.join(" and ")} requirements.`);
  }
  
  // Add similar courses teaser
  if (course.similar_courses && course.similar_courses.length > 0) {
    parts.push(`Explore related courses in ${course.course_reference.subjects[0]}.`);
  }
  
  return parts.filter(p => p.length > 0).join(" ");
}

export function generateCourseKeywords(
  course: Course,
  instructors: FullInstructorInformation[]
): string[] {
  const keywords: Set<string> = new Set();
  
  // Add course codes and variations
  keywords.add(courseReferenceToString(course.course_reference).toLowerCase());
  course.course_reference.subjects.forEach(subject => {
    keywords.add(subject.toLowerCase());
    keywords.add(`${subject} ${course.course_reference.course_number}`.toLowerCase());
  });
  
  // Add title words
  const titleWords = course.course_title.toLowerCase().split(/\s+/)
    .filter(word => word.length > 3 && !['with', 'from', 'this', 'that', 'through'].includes(word));
  titleWords.forEach(word => keywords.add(word));
  
  // Add level
  const courseNumber = course.course_reference.course_number;
  if (courseNumber < 300) keywords.add("introductory");
  else if (courseNumber < 500) keywords.add("intermediate");
  else if (courseNumber < 700) keywords.add("advanced");
  else keywords.add("graduate");
  
  // Add attributes
  const latestTerm = Object.keys(course.term_data).sort().reverse()[0];
  if (latestTerm && course.term_data[latestTerm]?.enrollment_data) {
    const enrollment = course.term_data[latestTerm].enrollment_data;
    if (enrollment.general_education) keywords.add("general education");
    if (enrollment.ethnic_studies) keywords.add("ethnic studies");
    if (enrollment.school?.name) keywords.add(enrollment.school.name.toLowerCase());
  }
  
  // Add UW-specific keywords
  keywords.add("uw madison");
  keywords.add("university of wisconsin");
  keywords.add("madison courses");
  
  // Add instructor names
  instructors.slice(0, 3).forEach(instructor => {
    keywords.add(instructor.name.toLowerCase());
  });
  
  return Array.from(keywords);
}

export function generateStructuredCourseTitle(course: Course): string {
  const courseCode = courseReferenceToString(course.course_reference);
  return `${courseCode}: ${course.course_title} - UW-Madison Course`;
}