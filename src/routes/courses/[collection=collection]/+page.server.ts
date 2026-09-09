import { course_collection } from "$lib/server/documents/course-collection";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(course_collection);
