import { query } from "$lib/server/data";
import { instructorUrls } from "$lib/server/instructor-urls";
import { courseUrl, courseTitle } from "$lib/format";
import { departmentName } from "$lib/departments";
import entries from "../../../.site/import/entries.json";
/** Build only social assets from small metadata records, without rendering pages. */
export async function socialManifest() {
  const [courses, instructors, urls] = await Promise.all([
    query(undefined, "SELECT code,title FROM courses ORDER BY code"),
    query(
      undefined,
      "SELECT uid,name FROM instructors WHERE name IS NOT NULL AND trim(name)!=''",
    ),
    instructorUrls(),
  ]);
  const card = (path: string, title: string, label: string) => ({
    path: `/social/pages${path}.png`,
    title,
    label,
  });
  const selected = new Set(entries.instructors);
  return [
    card("/stats", "UW–Madison by the numbers", "Campus stats"),
    ...courses.map((c) =>
      card(courseUrl(c.code), courseTitle(c.title), c.code),
    ),
    ...instructors
      .filter((i) => selected.has(i.uid))
      .map((i) => card(urls.get(i.uid)!, i.name, "Professor")),
    ...entries.subjects.flatMap((subject) => {
      const path = `/departments/${encodeURIComponent(subject)}`;
      const name = departmentName(subject);
      return [
        card(path, name, "Department"),
        card(`${path}/catalog`, name, "Course catalog"),
        card(`${path}/easiest`, name, "Easiest courses"),
        card(`${path}/hardest`, name, "Hardest courses"),
        card(
          `/explorer/${encodeURIComponent(subject)}`,
          name,
          "Prerequisite map",
        ),
      ];
    }),
  ];
}
