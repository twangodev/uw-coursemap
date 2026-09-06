import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import type { SubjectStats } from "$lib/types/subject-stats.ts";
import type { Terms } from "$lib/types/terms.ts";
import { getSubjectFullName } from "$lib/api.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

const { PUBLIC_API_URL } = env;

export const load = async ({ params, fetch }) => {
  const subject = params.subject.toUpperCase();

  const [subjectFullName, statsResponse, termsResponse] = await Promise.all([
    getSubjectFullName(fetch, subject),
    fetch(`${PUBLIC_API_URL}/stats/${subject}.json`),
    fetch(`${PUBLIC_API_URL}/terms.json`),
  ]);

  // a subject can exist in subjects.json before its stats file is generated
  let stats: SubjectStats | null = null;
  if (statsResponse.ok) {
    stats = await statsResponse.json();
  } else if (statsResponse.status !== 404) {
    throw error(
      statsResponse.status,
      `Failed to fetch subject statistics: ${statsResponse.statusText}`,
    );
  }

  if (!termsResponse.ok)
    throw error(
      termsResponse.status,
      `Failed to fetch terms: ${termsResponse.statusText}`,
    );
  const terms: Terms = await termsResponse.json();

  const ogImage = generateOgImageUrl({
    title: subject,
    subtitle: subjectFullName,
    description: `${subjectFullName} grade and enrollment statistics at UW-Madison`,
  });

  return {
    subtitle: `${subject} - Statistics`,
    ogImage,
    subject,
    subjectFullName,
    stats,
    terms,
  };
};
