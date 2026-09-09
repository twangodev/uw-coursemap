import { department_collection } from "$lib/server/documents/department-collection";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(department_collection);
