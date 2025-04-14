import type {GradeData} from "$lib/types/madgrades.ts";
import type {EnrollmentData} from "$lib/types/enrollment.ts";
import {apiFetch} from "$lib/api.ts";

export type CourseReference = {
    subjects: string[];
    course_number: number;
}

type CoursePrerequisites = {
    course_references: CourseReference[];
    prerequisites_text: string;
}

export type Course = {
    course_reference: CourseReference
    course_title: string
    description: string
    prerequisites: CoursePrerequisites,
    optimized_prerequisites: CoursePrerequisites,
    cumulative_grade_data: GradeData | null,
    term_data: {
        [key: string]: TermData,
    }
}

export type TermData = {
    enrollment_data: EnrollmentData | null,
    grade_data: GradeData | null,
}

export async function courseReferenceStringToCourse(sanatizedCourseReferenceString: string): Promise<Course> {
    let response =  await apiFetch(`/course/${sanatizedCourseReferenceString}.json`)
    return await response.json();
}

export function courseReferenceToString(courseReference: CourseReference): string {
    let subjects = [...courseReference.subjects].sort().join("/");
    return `${subjects} ${courseReference.course_number}`;
}

// This function is used to sanitize the course reference string for use in URLs
export function sanitizeCourseToReferenceString(courseReference: CourseReference): string {
    return courseReferenceToString(courseReference).replaceAll(" ", "_").replaceAll("/", "_");
}

export async function courseReferenceToCourse(courseReference: CourseReference): Promise<Course> {
    let sanitizedCourseReferenceToString = sanitizeCourseToReferenceString(courseReference);
    return await courseReferenceStringToCourse(sanitizedCourseReferenceToString);
}

export function getInstructorsWithEmail(course: Course | undefined, term: string): { [key: string]: string | null } {
    if (!course) return {};

    const termData = course.term_data[term];

    if (!termData) return {};

    const enrollmentData = termData.enrollment_data;
    if (enrollmentData) {
        return enrollmentData.instructors
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
}