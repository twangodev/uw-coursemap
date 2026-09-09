import { ZodError } from "zod";
import { building, dev } from "$app/environment";
import { redirect, isHttpError, type Handle } from "@sveltejs/kit";
import { representation, isDocument, alternateLinks } from "$lib/documents";
import { documentResponse } from "$lib/server/documents/response";
import { cachedResponse } from "$lib/server/response-cache";

export const handle: Handle = async ({ event, resolve }) => {
  const path = event.url.pathname;
  const search = building ? "" : event.url.search;
  if (path.startsWith("/subjects/"))
    redirect(308, "/departments/" + path.slice("/subjects/".length) + search);
  if (path === "/live" || path === "/upload") redirect(308, "/search" + search);
  const requested = representation(path);
  const render = async () => {
    if (requested) {
      try {
        return await documentResponse(event, requested);
      } catch (error) {
        const status = isHttpError(error) ? error.status : 500;
        if (status === 500) console.error("Document response failed", error);
        return new Response(
          JSON.stringify({
            error: isHttpError(error)
              ? error.body.message
              : "Document unavailable",
            ...(dev && error instanceof ZodError
              ? { issues: error.issues }
              : {}),
          }),
          {
            status,
            headers: {
              "Content-Type": "application/json",
              "X-Robots-Tag": "noindex",
              "Cache-Control": "no-store",
            },
          },
        );
      }
    }
    const response = await resolve(event);
    if (event.isDataRequest || path.startsWith("/api/"))
      response.headers.set("X-Robots-Tag", "noindex");
    if (
      !event.isDataRequest &&
      response.status === 200 &&
      isDocument(path) &&
      response.headers.get("content-type")?.includes("text/html")
    )
      response.headers.append("Link", alternateLinks(path, event.url.search));
    return response;
  };
  return !building && !dev && (requested || isDocument(path))
    ? cachedResponse(event, render)
    : render();
};
