import { query, status } from "./data";
import { buildCourseMap, type CourseMapData } from "$lib/course-map";
let cached: { revision: string; data: Promise<CourseMapData> } | undefined;
export async function courseMap(platform?: App.Platform, subject?: string) {
  const { revision } = await status(platform);
  if (!cached || cached.revision !== revision) {
    const data = query(
      platform,
      "SELECT uid,code,title,json_extract(payload,'$.subjects') subjects,json_extract(payload,'$.requirements') requirements FROM courses",
    ).then((rows) =>
      buildCourseMap(
        rows.map((row) => ({
          ...row,
          subjects: JSON.parse(row.subjects),
          requirements: JSON.parse(row.requirements || "null"),
        })),
      ),
    );
    cached = { revision, data };
    data.catch(() => {
      if (cached?.data === data) cached = undefined;
    });
  }
  const data = await cached.data;
  if (!subject) return data;
  const subjects = new Set(
    data.courses
      .filter((course) => course.subjects.includes(subject))
      .map((course) => course.uid),
  );
  const edges = data.edges.filter(
    (edge) => subjects.has(edge.source) || subjects.has(edge.target),
  );
  const visible = new Set([
    ...subjects,
    ...edges.flatMap((edge) => [edge.source, edge.target]),
  ]);
  return {
    courses: data.courses.filter((course) => visible.has(course.uid)),
    edges,
  };
}
