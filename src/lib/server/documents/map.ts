import type { DocumentContext } from "./types";
import { error } from "@sveltejs/kit";
import { courseMap } from "$lib/server/course-map";
import entriesData from "../../../../.site/import/entries.json";
export async function map({params,platform}: DocumentContext) {
 const subject = params.subject.toUpperCase();
 if (!entriesData.subjects.includes(subject)) error(404,"Department not found");
 return { subject, graph: await courseMap(platform, subject) };
}
