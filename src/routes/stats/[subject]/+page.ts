import { env } from "$env/dynamic/public";
import { error } from "@sveltejs/kit";
import type { SubjectStats } from "$lib/types/subject-stats.ts";
import type { Terms } from "$lib/types/terms.ts";
import { generateOgImageUrl } from "$lib/seo/og-image";

const { PUBLIC_API_URL } = env;

export const load = async ({ params, fetch }) => {
  const subject = params.subject.toUpperCase();

  const subjectsResponse = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  let subjectFullName = subject;
  if (subjectsResponse.ok) {
    const subjects = await subjectsResponse.json();
    subjectFullName = subjects[subject] || subject;
  }

  const statsResponse = await fetch(`${PUBLIC_API_URL}/stats/${subject}.json`);
  if (!statsResponse.ok)
    throw error(
      statsResponse.status,
      `Failed to fetch subject statistics: ${statsResponse.statusText}`,
    );
  const stats: SubjectStats = await statsResponse.json();

  const termsResponse = await fetch(`${PUBLIC_API_URL}/terms.json`);
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
