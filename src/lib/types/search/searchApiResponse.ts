export type SearchResponse = {

    courses: CourseSearchResponse[],
    instructors: InstructorSearchResponse[],
    subjects: SubjectSearchResponse[],

}


export type CourseSearchResponse = {
    course_id: string,
    course_title: string,
    course_number: number,
    subjects: string[],
    departments: string[],
}

export type InstructorSearchResponse = {
    instructor_id: string,
    name: string,
    official_name: string,
    email: string,
    position: string,
    department: string,
}

export type SubjectSearchResponse = {
    subject_id: string,
    name: string,
}


export function courseSearchResponseToIdentifier(course: CourseSearchResponse): string {
    let subjects = course.subjects.sort().join('/');
    return `${subjects} ${course.course_number}`;
}