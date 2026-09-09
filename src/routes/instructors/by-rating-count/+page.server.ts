import { instructors } from "$lib/server/documents/instructors";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(instructors);
