import {getLatestTermId, type Terms} from "$lib/types/terms.ts";
import {env} from "$env/dynamic/public";
import {getInstructorsWithEmail} from "$lib/types/course.ts";
import {apiFetch} from "$lib/api.ts";
import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ params, fetch }) => {

    let termsResponse = await fetch(`${PUBLIC_API_URL}/terms.json`)
    let terms: Terms = await termsResponse.json()
    let latestTermId = getLatestTermId(terms)

    let courseResponse = await fetch(`${PUBLIC_API_URL}/course/${params.courseIdentifier}.json`)
    let course = await courseResponse.json()

    return {
        terms: terms,
        selectedTermId: latestTermId,
        course: course,
    }

}