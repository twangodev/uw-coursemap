import { createApiClient } from "$lib/api";
import { error } from "@sveltejs/kit";
import type { ElementDefinition } from "cytoscape";
import { generateOgImageUrl } from "$lib/seo/og-image";

export const load = async ({ params, fetch }) => {
  const api = createApiClient(fetch);
  let subject = params.subject.toUpperCase();

  // Fetch subjects to get full name
  const { data: subjects } = await api.GET("/subjects");
  let subjectFullName = subjects?.[subject] || subject;

  const { data: graphData, error: graphError } = await api.GET("/graphs/{subject}", {
    params: { path: { subject } },
  });
  if (graphError || !graphData)
    throw error(404, `Failed to fetch graph data`);

  const elementDefinitions = graphData as unknown as ElementDefinition[];
  elementDefinitions.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      item.data["title"] = "";
    }
  });

  const { data: styleEntries, error: styleError } = await api.GET("/styles/{subject}", {
    params: { path: { subject } },
  });
  if (styleError || !styleEntries)
    throw error(404, `Failed to fetch style data`);

  const ogImage = generateOgImageUrl({
    title: subject,
    subtitle: subjectFullName,
    description: `${subjectFullName} course map and prerequisites at UW-Madison`,
  });

  return {
    subtitle: `${subject} - Explorer`,
    ogImage,
    elementDefinitions,
    styleEntries,
  };
};
