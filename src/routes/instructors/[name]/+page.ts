import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import type { FullInstructorInformation } from "$lib/types/instructor.ts";
import type { ProfilePage, WithContext } from "schema-dts";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ params, fetch }) => {
  const instructorName = params.name;

  const instructorResponse = await fetch(
    `${PUBLIC_API_URL}/instructors/${instructorName}.json`,
  );
  if (!instructorResponse.ok)
    throw error(
      instructorResponse.status,
      `Failed to fetch instructor: ${instructorResponse.statusText}`,
    );
  const instructor: FullInstructorInformation = await instructorResponse.json();

  const description = `${instructor.name} is a ${instructor.position || "faculty"} at ${instructor.department || "some department"} at the University of Wisconsin-Madison.`;

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
    subtitle: instructor.name,
    description: description,
    instructor: instructor,
    jsonLd: [jsonLd],
  };
};
