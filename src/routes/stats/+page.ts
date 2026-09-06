import { fetchSubjects } from "$lib/api.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

export const load = async ({ fetch }) => {
  const subjects: [string, string][] = Object.entries(
    await fetchSubjects(fetch),
  );

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
