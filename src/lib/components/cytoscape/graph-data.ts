import type { Course } from "$lib/types/course";
import type {
  EdgeDefinition,
  ElementDefinition,
  NodeDefinition,
} from "cytoscape";
import { apiFetch } from "$lib/api.ts";

/**
 * Process raw graph data by adding required properties for cytoscape
 * - Adds pannable property
 * - Adds empty title if missing
 * - Adds "course" class to course nodes (not edges or compound nodes)
 */
export function processGraphData(
  data: ElementDefinition[],
): ElementDefinition[] {
  data.forEach((item) => {
    item.pannable = true;
    item.data ??= {};
    if (!Object.hasOwn(item.data, "title")) {
      item.data.title = "";
    }
    if (
      item.data.id &&
      !item.data.source &&
      !item.data.target &&
      item.data.type !== "compound"
    ) {
      const classes = Array.isArray(item.classes)
        ? item.classes
        : (item.classes ?? "").split(/\s+/).filter(Boolean);
      item.classes = [...new Set([...classes, "course", "hoverable"])];
    }
  });
  return data;
}

/**
 * Fetch and process graph data from a URL (client-side use)
 */
export async function fetchGraphData(
  url: string,
): Promise<ElementDefinition[]> {
  const response = await fetch(url);
  const data = await response.json();
  return processGraphData(data);
}

export async function fetchCourse(courseId: string): Promise<Course> {
  // TODO use course.ts with sanatization
  const sanitizedId = courseId.replaceAll(" ", "_").replaceAll("/", "_");
  let response = await apiFetch(`/course/${sanitizedId}.json`);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch course ${courseId}: ${response.status} ${response.statusText}`,
    );
  }
  return response.json();
}

export function getNodeData(courseData: ElementDefinition[]): NodeDefinition[] {
  return courseData.filter((item) => "id" in item.data) as NodeDefinition[];
}
export function getEdgeData(courseData: ElementDefinition[]): EdgeDefinition[] {
  return courseData.filter((item) => "source" in item.data) as EdgeDefinition[];
}
