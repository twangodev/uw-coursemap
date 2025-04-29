import {getLatestTermId, type Terms} from "$lib/types/terms.ts";
import {env} from "$env/dynamic/public";
import {
    type Course,
    courseReferenceToString,
    sanitizeCourseToReferenceString
} from "$lib/types/course.ts";
import {apiFetch} from "$lib/api.ts";
import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";
import {error} from "@sveltejs/kit";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ params, url, fetch }) => {

    let termsResponse = await fetch(`${PUBLIC_API_URL}/terms.json`)
    if (!termsResponse.ok) throw error(termsResponse.status, `Failed to fetch terms: ${termsResponse.statusText}`)

    let terms: Terms = await termsResponse.json()
    let latestTermId = getLatestTermId(terms)
    let selectedTermId = url.searchParams.get('term') || latestTermId

    let courseResponse = await fetch(`${PUBLIC_API_URL}/course/${params.courseIdentifier}.json`)
    if (!courseResponse.ok) throw error(courseResponse.status, `Failed to fetch course: ${courseResponse.statusText}`)
    let course: Course = await courseResponse.json()

    let similarCourseReferences = course.similar_courses
    let similarCoursesPromises = similarCourseReferences.map(async (courseReference) => {
        let courseResponse = await fetch(`${PUBLIC_API_URL}/course/${sanitizeCourseToReferenceString(courseReference)}.json`)
        if (!courseResponse.ok) throw error(courseResponse.status, `Failed to fetch similar course: ${courseResponse.statusText}`)
        return await courseResponse.json()
    })
    let similarCourses: Course[] = await Promise.all(similarCoursesPromises)

    let instructors = await getFullInstructorInformation(course, terms, selectedTermId, fetch)

    return {
        terms: terms,
        selectedTermId: selectedTermId,
        course: course,
        similarCourses: similarCourses,
        instructors: instructors,
    }

}