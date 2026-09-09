import { department } from "$lib/server/documents/department";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(department);
