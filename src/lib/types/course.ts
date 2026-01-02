import type { components } from "$lib/types/api";
import { api } from "$lib/api";

// Re-export types from generated API
export type Course = components["schemas"]["Course"];
export type CourseReference = components["schemas"]["CourseReference"];
export type CoursePrerequisites = components["schemas"]["CoursePrerequisites"];
export type TermData = components["schemas"]["TermData"];

export const CourseUtils = {
  areEqual: (a: CourseReference, b: CourseReference): boolean => {
    return CourseUtils.courseReferenceToString(a) === CourseUtils.courseReferenceToString(b);
  },

  sanitizedStringToCourse: async (sanitizedCourseReferenceString: string): Promise<Course | null> => {
    const { data } = await api.GET("/course/{courseId}", {
      params: { path: { courseId: sanitizedCourseReferenceString } },
    });
    return data ?? null;
  },

  courseReferenceToString: (courseReference: CourseReference): string => {
    let subjects = [...courseReference.subjects].sort().join("/");
    return `${subjects} ${courseReference.course_number}`;
  },

  courseReferenceToSanitizedString: (courseReference: CourseReference): string => {
    return CourseUtils.courseReferenceToString(courseReference)
      .replaceAll(" ", "_")
      .replaceAll("/", "_");
  },

  courseReferenceToCourse: async (courseReference: CourseReference): Promise<Course> => {
    let sanitizedCourseReferenceString = CourseUtils.courseReferenceToSanitizedString(courseReference);
    const course = await CourseUtils.sanitizedStringToCourse(sanitizedCourseReferenceString);
    if (!course) {
      throw new Error(`Failed to fetch course: ${sanitizedCourseReferenceString}`);
    }
    return course;
  },

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