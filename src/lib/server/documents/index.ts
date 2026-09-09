import { building, dev } from "$app/environment";
import { readDocument, isFilteredDocument } from "./storage";
import { error } from "@sveltejs/kit";
import { home } from "./home";
import { course } from "./course";
import { course_collection } from "./course-collection";
import { instructor } from "./instructor";
import { instructors } from "./instructors";
import { search } from "./search";
import { department } from "./department";
import { department_collection } from "./department-collection";
import { catalog } from "./catalog";
import { map } from "./map";
import { maps } from "./maps";
import type { DocumentContext } from "./types";

/** Same loaders as +page.server.ts; no HTML scraping or Svelte transport decoding. */
export async function loadSourceDocument(context: DocumentContext) {
  const parts = context.url.pathname
    .split("/")
    .filter(Boolean)
    .map(decodeURIComponent);
  const [kind, id, child] = parts;
  if (!kind) return home(context);
  if (kind === "search" && parts.length === 1) return search(context);
  if ((kind === "departments" || kind === "explorer") && parts.length === 1)
    return {};
  if (kind === "courses" && parts.length === 2) {
    if (id === "easiest" || id === "hardest")
      return course_collection({ ...context, params: { collection: id } });
    return course({ ...context, params: { courseIdentifier: id } });
  }
  if (kind === "instructors" && parts.length === 2) {
    if (id === "by-rating-count") return instructors(context);
    return instructor({ ...context, params: { uid: id } });
  }
  if (kind === "departments" && id) {
    const next = { ...context, params: { subject: id, collection: child } };
    if (parts.length === 2) return department(next);
    if (parts.length === 3 && child === "catalog") return catalog(next);
    if (parts.length === 3 && (child === "easiest" || child === "hardest"))
      return department_collection(next);
  }
  if (kind === "explorer" && parts.length === 2)
    return id === "all"
      ? maps(context)
      : map({ ...context, params: { subject: id } });
  error(404, "Document not found");
}

export async function loadDocument(context: DocumentContext) {
  if (building || dev || isFilteredDocument(context.url))
    return loadSourceDocument(context);
  return (await readDocument(context.url, context.platform)).data;
}
