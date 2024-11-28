import type {MadgradesData} from "$lib/types/madgrades.ts";
import type {EnrollmentData} from "$lib/types/enrollment.ts";

type CourseReference = {
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
    madgrades_data: MadgradesData,
    enrollment_data: EnrollmentData,
}

export function courseReferenceToString(courseReference: CourseReference): string {
    let subjects = courseReference.subjects.sort().join("/");
    return `${subjects} ${courseReference.course_number}`;
}