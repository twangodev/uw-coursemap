import { aggregateTerms, cohortBenchmarks, type Benchmarks } from "$lib/grade-benchmarks";
import { building, dev } from "$app/environment";
import { query } from "./data";
import { compareCourse, type PeerCourse } from "$lib/course-context";

// Prerender shares one canonical catalog read and caches cohort summaries.
type Catalog = {
  groups: Map<string, PeerCourse[]>;
  courses: Map<string, PeerCourse>;
  benchmarks: Map<string, Benchmarks>;
  histories: Map<string, Benchmarks>;
};
let buildPeers: Promise<Catalog> | undefined;
function index(rows: PeerCourse[]): Catalog {
  const groups = new Map<string, PeerCourse[]>(),
    courses = new Map<string, PeerCourse>();
  for (const row of rows) {
    const key = row.term;
    const group = groups.get(key) || [];
    group.push(row);
    groups.set(key, group);
    courses.set(row.uid + ":" + row.term, row);
  }
  return { groups, courses, benchmarks: new Map([...groups].map(([term, rows]) => [term, cohortBenchmarks(rows)])), histories: new Map() };
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
    if (!count) return [];
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
        topShare: 100 * (counts[0] + counts[1]) / count,
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
      : index(await peers(platform));
  const current = catalog.courses.get(course.course_uid + ":" + term);
  if (!current) return null;
  const rows = catalog.groups.get(term) || [];
  const terms = [...new Set<string>(course.grades.map((row: any) => row.term_id))].sort();
  const historyKey = terms.join(",");
  let history = catalog.histories.get(historyKey);
  if (!history) {
    history = cohortBenchmarks(aggregateTerms(terms.flatMap((term) => catalog.groups.get(term) || [])));
    if (catalog.histories.size >= 128) catalog.histories.delete(catalog.histories.keys().next().value!);
    catalog.histories.set(historyKey, history);
  }
  const select = (values: Benchmarks = {}) => Object.fromEntries(["school", ...current.subjects].map((key) => [key, values[key] || null]));
  return {
    term,
    benchmarks: { all: select(history), terms: Object.fromEntries(terms.map((term) => [term, select(catalog.benchmarks.get(term))])) },
    gpa: current.gpa,
    count: current.count,
    university: compareCourse(current, rows),
    departments: current.subjects
      .map((subject) => ({
        subject,
        comparison: compareCourse(current, rows, subject),
      })),
  };
}
