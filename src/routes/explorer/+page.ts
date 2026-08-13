import { fetchSubjects } from "$lib/api.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

export const load = async ({ fetch }) => {
  const subjects: [string, string][] = Object.entries(
    await fetchSubjects(fetch),
  );

  const ogImage = generateOgImageUrl({
    title: "Course Explorer",
    subtitle: "UW-Madison",
    description: "Explore 10,000+ courses across 190+ departments",
  });

  return {
    subtitle: "Explorer",
    ogImage,
    subjects,
  };
};
