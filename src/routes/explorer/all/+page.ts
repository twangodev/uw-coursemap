import { createApiClient } from "$lib/api";
import { error } from "@sveltejs/kit";
import type { ElementDefinition } from "cytoscape";

export const load = async ({ fetch }) => {
  const api = createApiClient(fetch);

  const { data: graphData, error: graphError } = await api.GET("/global_graph");
  if (graphError || !graphData)
    throw error(404, `Failed to fetch graph data`);

  const elementDefinitions = graphData as unknown as ElementDefinition[];
  elementDefinitions.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      item.data["title"] = "";
    }
  });

  const { data: styleEntries, error: styleError } = await api.GET("/global_style");
  if (styleError || !styleEntries)
    throw error(404, `Failed to fetch style data`);

  return {
    elementDefinitions,
    styleEntries,
  };
};