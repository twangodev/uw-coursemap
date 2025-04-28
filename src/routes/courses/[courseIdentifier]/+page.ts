import {getLatestTermId, type Terms} from "$lib/types/terms.ts";
import {env} from "$env/dynamic/public";
import {getInstructorsWithEmail} from "$lib/types/course.ts";
import {apiFetch} from "$lib/api.ts";
import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ params, url, fetch }) => {

    let termsResponse = await fetch(`${PUBLIC_API_URL}/terms.json`)
    let terms: Terms = await termsResponse.json()
    let latestTermId = getLatestTermId(terms)
    let selectedTermId = url.searchParams.get('term') || latestTermId

    let courseResponse = await fetch(`${PUBLIC_API_URL}/course/${params.courseIdentifier}.json`)
    let course = await courseResponse.json()

    let instructors = await getFullInstructorInformation(course, terms, selectedTermId, fetch)

    return {
        terms: terms,
        selectedTermId: selectedTermId,
        course: course,
        instructors: instructors,
    }

}