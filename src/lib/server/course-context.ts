import { building, dev } from "$app/environment";
import { query } from "./data";
import { compareCourse, type PeerCourse } from "$lib/course-context";

// Prerender shares one catalog read; deployed fallback loads only the requested term.
type Catalog = {
  groups: Map<string, PeerCourse[]>;
  courses: Map<string, PeerCourse>;
};
let buildPeers: Promise<Catalog> | undefined;
function index(rows: PeerCourse[]): Catalog {
  const groups = new Map<string, PeerCourse[]>(),
    courses = new Map<string, PeerCourse>();
  for (const row of rows) {
    const key =
      row.term + ":" + Math.floor(Number(row.code.match(/(\d+)$/)?.[1]) / 100);
    const group = groups.get(key) || [];
    group.push(row);
    groups.set(key, group);
    courses.set(row.uid + ":" + row.term, row);
  }
  return { groups, courses };
}
async function peers(
  platform: App.Platform | undefined,
  term?: string,
): Promise<PeerCourse[]> {
  const rows = await query<any>(
    platform,
    `
    SELECT g.uid, c.code, g.term, g.payload,
      (SELECT json_group_array(subject) FROM subjects s WHERE s.uid=g.uid) subjects
    FROM grades g JOIN courses c ON c.uid=g.uid
    WHERE g.section='' ${term ? "AND g.term=?" : ""}`,
    term ? [term] : [],
  );
  return rows.flatMap((row) => {
    const record = JSON.parse(row.payload);
    const counts = ["a", "ab", "b", "bc", "c", "d", "f"].map(
      (key) => record[key] || 0,
    );
    const count = counts.reduce((sum, n) => sum + n, 0);
    if (count < 30) return [];
    const gpa =
      counts.reduce((sum, n, i) => sum + n * [4, 3.5, 3, 2.5, 2, 1, 0][i], 0) /
      count;
    return [
      {
        uid: row.uid,
        code: row.code,
        term: row.term,
        gpa,
        count,
        subjects: JSON.parse(row.subjects),
      },
    ];
  });
}

export async function courseContext(course: any, platform?: App.Platform) {
  const term = [...course.grades].sort((a, b) =>
    b.term_id.localeCompare(a.term_id),
  )[0]?.term_id;
  if (!term) return null;
  const catalog =
    building || dev
      ? await (buildPeers ??= peers(platform).then(index))
      : index(await peers(platform, term));
  const current = catalog.courses.get(course.course_uid + ":" + term);
  if (!current) return null;
  const key =
    term + ":" + Math.floor(Number(current.code.match(/(\d+)$/)?.[1]) / 100);
  const rows = catalog.groups.get(key) || [];
  return {
    term,
    gpa: current.gpa,
    count: current.count,
    university: compareCourse(current, rows),
    departments: current.subjects
      .map((subject) => ({
        subject,
        comparison: compareCourse(current, rows, subject),
      }))
      .filter((row) => row.comparison),
  };
}
