import { env } from "$env/dynamic/public";
import { generateOgImageUrl } from "$lib/seo/og-image";

const { PUBLIC_API_URL } = env;

export const load = async ({ fetch }) => {
  const subjectResponse = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  if (!subjectResponse.ok)
    throw new Error(`Failed to fetch subjects: ${subjectResponse.statusText}`);
  const subjects: [string, string][] = Object.entries(
    await subjectResponse.json(),
  );

  const ogImage = generateOgImageUrl({
    title: "Course Explorer",
    subtitle: "UW-Madison",
    description: "Explore 10,000+ courses across 190+ departments",
  });

  return {
    subtitle: "Explorer",
    ogImage: ogImage,
    subjects: subjects,
  };
};
