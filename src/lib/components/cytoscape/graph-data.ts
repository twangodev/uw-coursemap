import type { Course } from "$lib/types/course";
import type {
  EdgeDefinition,
  ElementDefinition,
  NodeDefinition,
} from "cytoscape";
import { api } from "$lib/api";

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
  const sanitizedId = courseId.replaceAll(" ", "_").replaceAll("/", "_");
  const { data } = await api.GET("/course/{courseId}", {
    params: { path: { courseId: sanitizedId } },
  });
  if (!data) throw new Error(`Failed to fetch course: ${courseId}`);
  return data;
}

export function getNodeData(courseData: ElementDefinition[]): NodeDefinition[] {
  return courseData.filter((item) => "id" in item.data) as NodeDefinition[];
}
export function getEdgeData(courseData: ElementDefinition[]): EdgeDefinition[] {
  return courseData.filter((item) => "source" in item.data) as EdgeDefinition[];
}
