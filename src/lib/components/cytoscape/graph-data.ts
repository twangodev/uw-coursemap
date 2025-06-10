import type { Course } from "$lib/types/course";
import type {
  EdgeDefinition,
  ElementDefinition,
  NodeDefinition,
} from "cytoscape";
import { apiFetch } from "$lib/api.ts";

export async function fetchGraphData(
  url: string,
): Promise<ElementDefinition[]> {
  let response = await fetch(url);
  let courseData = await response.json();
  courseData.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      // to avoid the warnings in console
      item.data["title"] = "";
    }
  });
  return courseData;
}

export async function fetchCourse(courseId: string): Promise<Course> {
  // TODO use course.ts with sanatization
  let response = await apiFetch(
    `/course/${courseId.replaceAll(" ", "_").replaceAll("/", "_")}.json`,
  );
  return response.json();
}

export function getNodeData(courseData: ElementDefinition[]): NodeDefinition[] {
  return courseData.filter((item) => "id" in item.data) as NodeDefinition[];
}
export function getEdgeData(courseData: ElementDefinition[]): EdgeDefinition[] {
  return courseData.filter((item) => "source" in item.data) as EdgeDefinition[];
}
