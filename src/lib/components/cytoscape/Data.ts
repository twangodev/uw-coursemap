import type { EdgeDefinition, ElementDefinition, NodeDefinition } from "cytoscape"

export async function fetchCourseData(url: string): Promise<ElementDefinition[]> {
    let response = await fetch(url);
    let courseData = await response.json();
    courseData.forEach((item: any) => {
        item['pannable'] = true;
    });
    return courseData
}
    
export function getNodeData(courseData: ElementDefinition[]): NodeDefinition[] { return courseData.filter((item) => !("source" in item.data)) as NodeDefinition[] }
export function getEdgeData(courseData: ElementDefinition[]): EdgeDefinition[] { return courseData.filter((item) => ("source" in item.data)) as EdgeDefinition[] }