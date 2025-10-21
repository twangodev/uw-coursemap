import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import type { ElementDefinition } from "cytoscape";
import { generateOgImageUrl } from "$lib/seo/og-image";

const { PUBLIC_API_URL } = env;

export const load = async ({ params, fetch }) => {
  let subject = params.subject.toUpperCase();

  // Fetch subjects to get full name
  const subjectsResponse = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  let subjectFullName = subject;
  if (subjectsResponse.ok) {
    const subjects = await subjectsResponse.json();
    subjectFullName = subjects[subject] || subject;
  }

  const elementDefinitionsResponse = await fetch(
    `${PUBLIC_API_URL}/graphs/${subject}.json`,
  );
  if (!elementDefinitionsResponse.ok)
    throw error(
      elementDefinitionsResponse.status,
      `Failed to fetch graph data: ${elementDefinitionsResponse.statusText}`,
    );
  const elementDefinitions: ElementDefinition[] =
    await elementDefinitionsResponse.json();

  elementDefinitions.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      item.data["title"] = "";
    }
  });

  const styleEntriesResponse = await fetch(
    `${PUBLIC_API_URL}/styles/${subject}.json`,
  );
  if (!styleEntriesResponse.ok)
    throw error(
      styleEntriesResponse.status,
      `Failed to fetch style data: ${styleEntriesResponse.statusText}`,
    );
  const styleEntries = await styleEntriesResponse.json();

  const ogImage = generateOgImageUrl({
    title: subject,
    subtitle: subjectFullName,
    description: `Course map and prerequisites at UW-Madison`,
  });

  return {
    subtitle: `${subject} - Explorer`,
    ogImage: ogImage,
    elementDefinitions: elementDefinitions,
    styleEntries: styleEntries,
  };
};
