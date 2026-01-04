import { env } from "$env/dynamic/public";
import createClient from "openapi-fetch";
import type { paths } from "$lib/types/api";

const PUBLIC_API_URL = env.PUBLIC_API_URL;
const PUBLIC_SEARCH_API_URL = env.PUBLIC_SEARCH_API_URL;

/**
 * Type-safe API client using the global fetch.
 * Use this for client-side code outside of load functions.
 *
 * Usage:
 * ```ts
 * const { data, error } = await api.GET("/course/{courseId}", {
 *   params: { path: { courseId: "COMPSCI_200" } }
 * });
 * ```
 */
export const api = createClient<paths>({
  baseUrl: PUBLIC_API_URL,
});

/**
 * Create a type-safe API client with a custom fetch function.
 * Use this in SvelteKit load functions to pass the provided fetch.
 *
 * Usage:
 * ```ts
 * export const load = async ({ fetch }) => {
 *   const client = createApiClient(fetch);
 *   const { data } = await client.GET("/course/{courseId}", {
 *     params: { path: { courseId: "COMPSCI_200" } }
 *   });
 * };
 * ```
 */
export function createApiClient(fetchFn: typeof fetch) {
  return createClient<paths>({
    baseUrl: PUBLIC_API_URL,
    fetch: fetchFn,
  });
}

// Search API (not part of static API)
export async function getRandomCourses(): Promise<Response> {
  return await fetch(`${PUBLIC_SEARCH_API_URL}/random-courses`);
}

export async function search(query: string): Promise<Response> {
  return await fetch(`${PUBLIC_SEARCH_API_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: query }),
  });
}