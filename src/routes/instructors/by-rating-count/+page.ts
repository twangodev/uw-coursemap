import type {QuickStatistics} from "$lib/types/misc.ts";
import {env} from "$env/dynamic/public";
import type {FullInstructorInformation} from "$lib/types/instructor.ts";

const {PUBLIC_API_URL} = env

export const load = async ({ fetch }) => {

    const quickStatisticsResponse = await fetch(`${PUBLIC_API_URL}/quick_statistics.json`);
    if (!quickStatisticsResponse.ok) throw new Error(`Failed to fetch quick statistics: ${quickStatisticsResponse.statusText}`);
    const quickStatistics: QuickStatistics = await quickStatisticsResponse.json();

    const instructorNames = quickStatistics.most_rated_instructors
    const instructors: FullInstructorInformation[] = await Promise.all(instructorNames.map(async (name) => {
        const sanitized = name.replaceAll(" ", "_").replaceAll("/", "_");
        const response = await fetch(`${PUBLIC_API_URL}/instructors/${sanitized}.json`)
        if (!response.ok) throw new Error(`Failed to fetch instructor: ${response.statusText}`);
        return await response.json();
    })) // Not efficient at all without server side caching, but this is a TODO i dont have time for this right now problem. womp womp

    return {
        subtitle: 'Most Rated Instructors',
        instructors: instructors
    }

}