import { error } from "@sveltejs/kit";
import { query, pageData } from "./data";
export async function instructorReviews(
  uid: string,
  page = 1,
  course = "",
  platform?: App.Platform,
) {
  if (!Number.isInteger(page) || page < 1 || page > 10000)
    error(400, "Invalid page");
  const instructor = await pageData("instructors", uid, platform);
  const profile = instructor.ratings?.profile_id;
  if (!profile)
    return { items: [], total: 0, page, courses: [], matched: false };
  const values: unknown[] = [profile];
  let where = "profile_id=?";
  if (course) {
    where += " AND course_uid=?";
    values.push(course);
  }
  const [count, rows, courses] = await Promise.all([
    query(
      platform,
      `SELECT count(*) total FROM reviews WHERE ${where}`,
      values,
    ),
    query(
      platform,
      `SELECT payload FROM reviews WHERE ${where} ORDER BY review_date DESC,review_id LIMIT 6 OFFSET ?`,
      [...values, (page - 1) * 6],
    ),
    query(
      platform,
      "SELECT DISTINCT r.course_uid,c.code course_id FROM reviews r JOIN courses c ON c.uid=r.course_uid WHERE r.profile_id=? ORDER BY c.code",
      [profile],
    ),
  ]);
  return {
    items: rows.map((row) => JSON.parse(row.payload)),
    total: count[0].total,
    page,
    courses,
    matched: true,
  };
}
