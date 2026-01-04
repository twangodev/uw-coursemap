import { createApiClient } from "$lib/api";
import { error } from "@sveltejs/kit";
import type { ProfilePage, WithContext } from "schema-dts";
import { generateInstructorMetaDescription, generateInstructorTitle, generateInstructorOgImage } from "$lib/seo/instructor-seo.ts";

export const load = async ({ params, fetch }) => {
  const api = createApiClient(fetch);
  const instructorName = params.name;

  const { data, error: fetchError } = await api.GET("/instructors/{instructorId}", {
    params: { path: { instructorId: instructorName } },
  });
  if (fetchError || !data)
    throw error(404, `Failed to fetch instructor`);

  const instructor = data;

  const description = generateInstructorMetaDescription(instructor);
  const pageTitle = generateInstructorTitle(instructor);
  const ogImage = generateInstructorOgImage(instructor);

  const jsonLd: WithContext<ProfilePage> = {
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    mainEntity: {
      "@type": "Person",
      name: instructor.name,
      jobTitle: instructor.position || "Faculty",
      affiliation: {
        "@type": "EducationalOrganization",
        name: "University of Wisconsin-Madison",
        department: instructor.department || "Some Department",
      },
    },
  };

  return {
    subtitle: pageTitle,
    description,
    ogImage,
    instructor,
    jsonLd: [jsonLd],
  };
};
