import { env } from "$env/dynamic/public";
import type { Course } from "./types/course";
import type { SearchResponse } from "./types/search/searchApiResponse";

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

export async function getCourse(courseCode: string) {
  try {
    const response = await apiFetch(`/course/${courseCode}.json`);
    if (response.ok) {
      let res = await response.json();
      if (res) return res;
    }
    console.log("Course not found in main API, searching...");
    console.log("courseCode:", courseCode);
    // TODO: This is kinda scuffed but will work for now
    const searchResponse = await search(courseCode);
    const data: SearchResponse = await searchResponse.json();

    console.log("data:",data);
    const rawCourses = data.courses;
    let targetCourse = rawCourses[0];
    let course = {
      "course_reference": {
        "subjects": targetCourse.subjects,
        "course_number": targetCourse.course_number
      },
      "course_title": targetCourse.course_title,
    }
    return course;
  } catch (e) {
    console.log(e);
    return null;
  }
}
