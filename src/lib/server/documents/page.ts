import { building, dev } from "$lib/server/runtime";
import { readDocument, isFilteredDocument } from "./storage";
import type { DocumentContext } from "./types";

/** Pages and public representations consume the same build-validated document. */
export function pageDocument<T>(
  source: (context: DocumentContext) => Promise<T>,
) {
  return async (context: DocumentContext): Promise<T> => {
    if (building || dev || isFilteredDocument(context.url))
      return source(context);
    return (await readDocument(context.url, context.platform)).data as T;
  };
}
