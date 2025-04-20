import type { LayoutServerLoad } from './$types';
import { getContributors } from '$lib/github';

export const load: LayoutServerLoad = async () => {
    const contributors = (await getContributors()).slice(0,5);
    return { contributors };
};