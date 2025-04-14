import type {
    CourseSearchResponse,
    InstructorSearchResponse,
    SubjectSearchResponse
} from "$lib/types/search/searchApiResponse.ts";

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


export type UnifiedSearchResponse = {
    type: "course" | "instructor" | "subject",
    data: CourseSearchResult | SubjectSearchResult | InstructorSearchResult,
}

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

export function combineSearchResults(
    courses: CourseSearchResponse[],
    subjects: SubjectSearchResponse[],
    instructors: InstructorSearchResponse[]
): UnifiedSearchResponse[] {
    const courseResults: UnifiedSearchResponse[] = generateCourseSearchResults(courses).map(result => ({
        type: "course",
        data: result
    }));

    const subjectResults: UnifiedSearchResponse[] = generateSubjectSearchResults(subjects).map(result => ({
        type: "subject",
        data: result
    }));

    const instructorResults: UnifiedSearchResponse[] = generateInstructorSearchResults(instructors).map(result => ({
        type: "instructor",
        data: result
    }));

    const unsortedResults = [...courseResults, ...subjectResults, ...instructorResults];

    return unsortedResults.sort((a, b) => {
        return (b.data.score ?? 0) - (a.data.score ?? 0);
    });
}