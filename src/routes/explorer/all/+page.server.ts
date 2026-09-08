import { courseMap } from "$lib/server/course-map";
export const prerender = true;
export async function load({platform}) { return {subject:null, graph:await courseMap(platform)}; }
