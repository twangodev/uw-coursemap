import { building, dev } from "$app/environment";
import { status } from "$lib/server/data";
import { redirect, type Handle } from "@sveltejs/kit";
/** Preserve useful bookmarks from the previous frontend. */
export const handle: Handle = async ({ event, resolve }) => {
  const path = event.url.pathname;
  if (path.startsWith("/subjects/"))
    redirect(308, "/departments/" + path.slice("/subjects/".length) + event.url.search);
  // These retired tools now lead to the course browser.
  if (path === "/live" || path === "/upload")
    redirect(308, "/search" + event.url.search);
  if (
    !building &&
    !dev &&
    event.platform &&
    event.request.method === "GET" &&
    path.startsWith("/instructors/") &&
    !path.endsWith("__data.json")
  ) {
    const dataset = await status(event.platform);
    const keyUrl = new URL(event.url);
    keyUrl.searchParams.set(
      "_release",
      dataset.revision + ":" + (event.platform.env.SITE_COMMIT || "initial"),
    );
    const key = new Request(keyUrl);
    const cache = (caches as CacheStorage & { default: Cache }).default;
    const hit = await cache.match(key);
    if (hit) return hit;
    const response = await resolve(event);
    if (response.status === 200)
      event.platform.context.waitUntil(cache.put(key, response.clone()));
    return response;
  }
  return resolve(event);
};
