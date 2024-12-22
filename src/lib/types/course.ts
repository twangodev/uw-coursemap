import type {MadgradesData} from "$lib/types/madgrades.ts";
import type {EnrollmentData} from "$lib/types/enrollment.ts";
import {PUBLIC_API_URL} from "$env/static/public";

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
    madgrades_data: MadgradesData | null,
    enrollment_data: EnrollmentData | null,
}

export async function courseReferenceStringToCourse(sanatizedCourseReferenceString: string): Promise<Course> {
    let response = await fetch(`${PUBLIC_API_URL}/course/${sanatizedCourseReferenceString}.json`)
    return await response.json();
}

export function courseReferenceToString(courseReference: CourseReference): string {
    let subjects = courseReference.subjects.sort().join("/");
    return `${subjects} ${courseReference.course_number}`;
}

export function sanitizeCourseToReferenceString(courseReference: CourseReference): string {
    return courseReferenceToString(courseReference).replaceAll(" ", "_").replaceAll("/", "_");
}

export async function courseReferenceToCourse(courseReference: CourseReference): Promise<Course> {
    let sanitizedCourseReferenceToString = sanitizeCourseToReferenceString(courseReference);
    return await courseReferenceStringToCourse(sanitizedCourseReferenceToString);
}