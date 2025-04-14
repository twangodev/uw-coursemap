import type {UnifiedSearchResponse} from "$lib/types/search/searchResults.ts";

export type SearchResponse = {
    courses: CourseSearchResponse[],
    instructors: InstructorSearchResponse[],
    subjects: SubjectSearchResponse[],
}

type ScoredSearch = {
    score: number,
}

export type CourseSearchResponse = ScoredSearch & {
    course_id: string,
    course_title: string,
    course_number: number,
    subjects: string[],
    departments: string[],
}

export type InstructorSearchResponse = ScoredSearch & {
    instructor_id: string,
    name: string,
    official_name: string,
    email: string,
    position: string,
    department: string,
}

export type SubjectSearchResponse = ScoredSearch & {
    subject_id: string,
    name: string,
}

export function searchResponseToIdentifier(unifiedSearchResponse: UnifiedSearchResponse): string {
    if (unifiedSearchResponse.type !== "course") {
        return '';
    }
    let courseData = unifiedSearchResponse.data as CourseSearchResponse;
    let subjects = courseData.subjects.sort().join('/');
    return `${subjects} ${courseData.course_number}`;
}