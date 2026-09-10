import { dev } from "$app/environment";
import type { RequestHandler } from "./$types";
import { apiJson } from "$lib/server/api-response";
import { weatherSchema } from "$lib/api/schemas";
import { madisonWeather } from "$lib/server/weather";

export const GET: RequestHandler = async ({ platform, url }) => {
  const cache =
    !dev && platform
      ? (caches as CacheStorage & { default: Cache }).default
      : null;
  const key = new Request(new URL("/api/weather", url.origin));
  const hit = await cache?.match(key);
  if (hit) return hit;
  const data = await madisonWeather();
  const response = apiJson(weatherSchema, data, {
    headers: {
      "Cache-Control": `public, max-age=${data.available ? 900 : 60}`,
      "X-Robots-Tag": "noindex",
    },
  });
  if (cache && platform)
    platform.context.waitUntil(
      cache
        .put(key, response.clone())
        .catch((error) => console.error("Weather cache write failed", error)),
    );
  return response;
};
