import { env } from "$env/dynamic/public";

const PUBLIC_API_URL = env.PUBLIC_API_URL;
const PUBLIC_SEARCH_API_URL = env.PUBLIC_SEARCH_API_URL;

export async function apiFetch(path: string): Promise<Response> {
  return await fetch(`${PUBLIC_API_URL}${path}`);
}

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