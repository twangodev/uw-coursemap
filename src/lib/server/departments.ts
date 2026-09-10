import { building, dev } from "$lib/server/runtime";
import { query } from "./data";
import { gradeKeys, gradeSummary } from "$lib/discovery";
let cached: Promise<any[]> | undefined;
const sums = gradeKeys.map((key) => `SUM(g.${key}) ${key}`).join(",");
const aggregateSql = `SELECT g.term,c.number/100*100 number,${sums} FROM grade_summaries g JOIN course_numbers c ON c.uid=g.uid`;
async function catalog(platform?: App.Platform) {
  const read = () =>
    query(platform, `${aggregateSql} GROUP BY g.term,c.number/100`);
  return building || dev ? await (cached ??= read()) : await read();
}
export async function departmentStats(
  subject: string,
  platform?: App.Platform,
) {
  const [catalogRows, own, offeringRows, teachingRows] = await Promise.all([
    catalog(platform),
    query(
      platform,
      `${aggregateSql} JOIN subjects s ON s.uid=g.uid WHERE s.subject=? GROUP BY g.term,c.number/100`,
      [subject],
    ),
    query(
      platform,
      "SELECT o.term,count(DISTINCT o.uid) courses FROM offerings o JOIN subjects s ON s.uid=o.uid WHERE s.subject=? GROUP BY o.term",
      [subject],
    ),
    query(
      platform,
      "SELECT t.term,count(DISTINCT t.instructor_uid) instructors FROM teaching t JOIN subjects s ON s.uid=t.course_uid WHERE s.subject=? GROUP BY t.term",
      [subject],
    ),
  ]);
  const terms = [
    ...new Set([
      ...own.map((row) => row.term),
      ...offeringRows.map((row) => row.term),
      ...teachingRows.map((row) => row.term),
    ]),
  ].sort();
  const summarized = (term?: string) => {
    const rows = term ? own.filter((row) => row.term === term) : own;
    const covered = new Set(rows.map((row) => row.term));
    const peers = catalogRows.filter((row) =>
      term ? row.term === term : covered.has(row.term),
    );
    return {
      ...gradeSummary(rows),
      university: gradeSummary(peers),
      courses: offeringRows.find((row) => row.term === term)?.courses ?? null,
      instructors:
        teachingRows.find((row) => row.term === term)?.instructors ?? 0,
      levels: Array.from({ length: 10 }, (_, i) => ({
        level: `${i * 100}–${i * 100 + 99}`,
        ...gradeSummary(
          rows.filter((row) => Math.floor(row.number / 100) === i),
        ),
        university: gradeSummary(
          peers.filter((row) => Math.floor(row.number / 100) === i),
        ),
      })).filter((row) => row.count),
    };
  };
  return {
    all: summarized(),
    terms: Object.fromEntries(terms.map((term) => [term, summarized(term)])),
  };
}
