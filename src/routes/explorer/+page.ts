import { env } from "$env/dynamic/public";

const { PUBLIC_API_URL } = env;

export const load = async ({ fetch }) => {
  const subjectResponse = await fetch(`${PUBLIC_API_URL}/subjects.json`);
  if (!subjectResponse.ok)
    throw new Error(`Failed to fetch subjects: ${subjectResponse.statusText}`);
  const subjects: [string, string][] = Object.entries(
    await subjectResponse.json(),
  );

  return {
    subtitle: "Explorer",
    subjects: subjects,
  };
};
