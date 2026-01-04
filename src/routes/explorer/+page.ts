import { createApiClient } from "$lib/api";
import { generateOgImageUrl } from "$lib/seo/og-image";

export const load = async ({ fetch }) => {
  const api = createApiClient(fetch);
  const { data, error } = await api.GET("/subjects");
  if (error || !data)
    throw new Error(`Failed to fetch subjects`);
  const subjects: [string, string][] = Object.entries(data);

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
