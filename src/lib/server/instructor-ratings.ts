import { instructorUrls } from "./instructor-urls";
import { query } from "./data";
import { adjustInstructorRating } from "$lib/instructor-ratings";
import { building, dev } from "$app/environment";
import { error } from "@sveltejs/kit";
import { readAsset } from "./documents/storage";
let cached: { revision: string; mean: Promise<number | null> } | undefined;
export async function instructorRatingPrior(platform?: App.Platform) {
  if (!building && !dev) {
    const stored = await readAsset<{ mean: number | null }>(
      "/__documents/search-metadata.json",
      platform,
    );
    if (!stored) error(503, "Published search metadata unavailable");
    return stored.mean;
  }
  const [metadata] = await query(
    platform,
    "SELECT json_extract(value,'$.revision') revision FROM metadata WHERE key='status'",
  );
  const revision = metadata?.revision;
  if (!cached || cached.revision !== revision) {
    const mean = query(
      platform,
      "SELECT AVG(json_extract(payload,'$.quality_rating')) mean FROM reviews WHERE json_extract(payload,'$.quality_rating') BETWEEN 1 AND 5",
    ).then(([row]) => row?.mean ?? null);
    cached = { revision, mean };
    mean.catch(() => {
      if (cached?.mean === mean) cached = undefined;
    });
  }
  return cached.mean;
}
export async function withInstructorRatings(
  data: any,
  kind: string,
  platform?: App.Platform,
) {
  const [prior, urls] = await Promise.all([
    instructorRatingPrior(platform),
    instructorUrls(platform),
  ]);
  const adjust = (instructor: any) => ({
    ...instructor,
    instructor_url: urls.get(instructor.instructor_uid),
    ratings: adjustInstructorRating(instructor.ratings, prior),
  });
  return kind === "instructors"
    ? adjust(data)
    : {
        ...data,
        instructors: (data.instructors || []).map(adjust),
        grade_instructors: (data.grade_instructors || []).map(adjust),
      };
}
