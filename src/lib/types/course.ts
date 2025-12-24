import type { GradeData } from "$lib/types/madgrades.ts";
import type { EnrollmentData } from "$lib/types/enrollment.ts";
import { apiFetch } from "$lib/api.ts";

export type CourseReference = {
  subjects: string[];
  course_number: number;
};

type CoursePrerequisites = {
  course_references: CourseReference[];
  prerequisites_text: string;
  linked_requisite_text: (string | CourseReference)[];
};

export type Course = {
  course_reference: CourseReference;
  course_title: string;
  description: string;
  prerequisites: CoursePrerequisites;
  optimized_prerequisites: CoursePrerequisites;
  cumulative_grade_data: GradeData | null;
  term_data: {
    [key: string]: TermData;
  };
  similar_courses: CourseReference[];
  satisfies: CourseReference[];
};

export type TermData = {
  enrollment_data: EnrollmentData | null;
  grade_data: GradeData | null;
};

export const CourseUtils = {

  sanitizedStringToCourse: async (sanitizedCourseReferenceString: string): Promise<Course> => {
    const response = await apiFetch(
      `/course/${sanitizedCourseReferenceString}.json`,
    );
    return await response.json();
  },

  courseReferenceToString: (courseReference: CourseReference): string => {
    let subjects = [...courseReference.subjects].sort().join("/");
    return `${subjects} ${courseReference.course_number}`;
  },

  // This function is used to sanitize the course reference string for use in URLs
  courseReferenceToSanitizedString: (courseReference: CourseReference): string => {
    return CourseUtils.courseReferenceToString(courseReference)
      .replaceAll(" ", "_")
      .replaceAll("/", "_");
  },

  courseReferenceToCourse: async (courseReference: CourseReference): Promise<Course> => {
    let sanitizedCourseReferenceString = CourseUtils.courseReferenceToSanitizedString(courseReference);
    return await CourseUtils.sanitizedStringToCourse(sanitizedCourseReferenceString);
  },

  /**
   * Get the latest term key from a course's term data
   * Returns null if no terms exist
   */
  getLatestTermKey: (course: Course): string | null => {
    const termKeys = Object.keys(course.term_data).sort().reverse();
    return termKeys.length > 0 ? termKeys[0] : null;
  },

  getInstructorsWithEmail: (course: Course, term: string): { [key: string]: string | null } => {
    const termData = course.term_data[term];
    if (!termData) return {};
    const enrollmentData = termData.enrollment_data;
    if (enrollmentData) {
      return enrollmentData.instructors;
    }

    const gradesData = termData.grade_data;
    if (gradesData) {
      const names = gradesData.instructors;
      if (!names) return {};
      const instructorWithEmail: { [key: string]: string | null } = {};
      for (const name of names) {
        instructorWithEmail[name] = null;
      }
      return instructorWithEmail;
    }
    return {};
  },

  getLatestInstructorNames: (course: Course): string[] => {
    const latestTerm = CourseUtils.getLatestTermKey(course);
    if (!latestTerm) return [];
    const instructorsWithEmail = CourseUtils.getInstructorsWithEmail(course, latestTerm);
    return Object.keys(instructorsWithEmail);
  }
};
