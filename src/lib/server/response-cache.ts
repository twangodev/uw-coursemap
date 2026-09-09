import type { RequestEvent } from "@sveltejs/kit";

/** A release-addressed key prevents serving an old projection after a deployment. */
export function responseCacheKey(url: URL, release: string) {
  const key = new URL(url);
  key.searchParams.sort();
  key.pathname =
    "/__response-cache/" + encodeURIComponent(release) + key.pathname;
  return new Request(key);
}
export async function cachedResponse(
  event: RequestEvent,
  render: () => Promise<Response>,
) {
  const env = event.platform?.env;
  const release =
    env?.SITE_COMMIT && env.DATA_PROJECTION
      ? `${env.SITE_COMMIT}:${env.DATA_PROJECTION}`
      : null;
  // Navigation transport depends on invalidation headers. Never share it with documents.
  if (
    !release ||
    !event.platform ||
    event.isDataRequest ||
    event.request.method !== "GET" ||
    event.request.headers.has("authorization") ||
    event.request.headers.has("cookie")
  )
    return render();
  const cache = (caches as CacheStorage & { default: Cache }).default;
  const key = responseCacheKey(event.url, release);
  const hit = await cache.match(key);
  const respond = (response: Response, state: string) => {
    const headers = new Headers(response.headers);
    headers.set("Cache-Control", "public, max-age=0, must-revalidate");
    headers.set("X-Cache", state);
    if (event.request.headers.get("if-none-match") === headers.get("etag"))
      return new Response(null, { status: 304, headers });
    return new Response(response.body, { status: response.status, headers });
  };
  if (hit) return respond(hit, "HIT");
  const response = await render();
  if (
    response.status !== 200 ||
    response.headers.has("set-cookie") ||
    /private|no-store/i.test(response.headers.get("cache-control") || "")
  )
    return response;
  const body = await response.arrayBuffer();
  const headers = new Headers(response.headers);
  const digest = await crypto.subtle.digest("SHA-256", body);
  headers.set(
    "ETag",
    '"' +
      Array.from(new Uint8Array(digest), (b) =>
        b.toString(16).padStart(2, "0"),
      ).join("") +
      '"',
  );
  headers.set("Cache-Control", "public, max-age=86400");
  const stored = new Response(body, { headers });
  event.platform.context.waitUntil(
    cache
      .put(key, stored.clone())
      .catch((error) => console.error("Response cache write failed", error)),
  );
  return respond(stored, "MISS");
}
