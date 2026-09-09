import { search } from "$lib/server/documents/search";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(search);
