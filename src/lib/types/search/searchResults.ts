import type {
    CourseSearchResponse,
    InstructorSearchResponse,
    SubjectSearchResponse
} from "$lib/types/search/searchApiResponse.ts";
import {type Course, courseReferenceToString} from "$lib/types/course.ts";

type HrefResult<T> = T & {
    href: string,
}

export type CourseSearchResult = HrefResult<CourseSearchResponse> & {
    explorerHref: {
        [key: string]: string
    }
}
export type SubjectSearchResult =  HrefResult<SubjectSearchResponse>;
export type InstructorSearchResult = HrefResult<InstructorSearchResponse>;

export function generateCourseSearchResults(courses: CourseSearchResponse[]): CourseSearchResult[] {
    return courses.map(course => ({
        ...course,
        href: `/courses/${course.course_id}`,
        explorerHref: Object.fromEntries(
            course.subjects.map(subject => [subject, `/explorer/${subject}?focus=${course.course_id}`])
        )
    }));
}

export function generateSubjectSearchResults(subjects: SubjectSearchResponse[]): SubjectSearchResult[] {
    return subjects.map(subject => ({
        ...subject,
        href: `/explorer/${subject.subject_id}`
    }));
}

export function generateInstructorSearchResults(instructors: InstructorSearchResponse[]): InstructorSearchResult[] {
    return instructors.map(instructor => ({
        ...instructor,
        href: `/instructors/${instructor.instructor_id}`
    }));
}