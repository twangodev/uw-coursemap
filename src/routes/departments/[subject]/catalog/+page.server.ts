import { catalog } from "$lib/server/documents/catalog";
import { pageDocument } from "$lib/server/documents/page";
export const load = pageDocument(catalog);
