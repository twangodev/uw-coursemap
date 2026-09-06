import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";

const PUBLIC_API_URL = env.PUBLIC_API_URL;
const PUBLIC_SEARCH_API_URL = env.PUBLIC_SEARCH_API_URL;

export async function apiFetch(path: string): Promise<Response> {
  return await fetch(`${PUBLIC_API_URL}${path}`);
}

// takes the load-provided fetch so it works during SSR
export async function fetchSubjects(
  fetch: typeof globalThis.fetch,
): Promise<Record<string, string>> {
  const response = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  if (!response.ok)
    throw error(
      response.status,
      `Failed to fetch subjects: ${response.statusText}`,
    );
  return await response.json();
}

export async function getSubjectFullName(
  fetch: typeof globalThis.fetch,
  subject: string,
): Promise<string> {
  const response = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  if (!response.ok) return subject;
  const subjects = await response.json();
  return subjects[subject] || subject;
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
