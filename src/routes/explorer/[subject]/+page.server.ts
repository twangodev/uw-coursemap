import { error } from "@sveltejs/kit";
import { courseMap } from "$lib/server/course-map";
import entriesData from "../../../../.site/entries.json";
export const prerender = "auto";
export const entries = () => entriesData.subjects.map(subject => ({subject}));
export async function load({params,platform}) {
 const subject = params.subject.toUpperCase();
 if (!entriesData.subjects.includes(subject)) error(404,"Department not found");
 return { subject, graph: await courseMap(platform, subject) };
}
