import {env} from "$env/dynamic/public";
import {error} from "@sveltejs/kit";
import type {FullInstructorInformation} from "$lib/types/instructor.ts";

const PUBLIC_API_URL = env.PUBLIC_API_URL

export const load = async ({ params, fetch }) => {

    const instructorName = params.name

    const instructorResponse = await fetch(`${PUBLIC_API_URL}/instructors/${instructorName}.json`);
    if (!instructorResponse.ok) throw error(instructorResponse.status, `Failed to fetch instructor: ${instructorResponse.statusText}`)
    const instructor: FullInstructorInformation = await instructorResponse.json();

    return {
        instructor: instructor
    }
};