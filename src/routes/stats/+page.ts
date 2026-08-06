import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import { generateOgImageUrl } from "$lib/seo/og-image";

const { PUBLIC_API_URL } = env;

export const load = async ({ fetch }) => {
  const subjectsResponse = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  if (!subjectsResponse.ok)
    throw error(
      subjectsResponse.status,
      `Failed to fetch subjects: ${subjectsResponse.statusText}`,
    );
  const subjectEntries: [string, string][] = Object.entries(
    await subjectsResponse.json(),
  );
  const subjects = subjectEntries.sort(([, a], [, b]) => a.localeCompare(b));

  const ogImage = generateOgImageUrl({
    title: "Departmental Statistics",
    subtitle: "UW-Madison",
    description: "Grade and enrollment trends for every department",
  });

  return {
    subtitle: "Statistics",
    ogImage,
    subjects,
  };
};
