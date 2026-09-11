import { selectStatsTerm } from "./stats-selection";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { query, status } from "$lib/server/data";
import {
  emptySchoolTerm,
  gradeTotals,
  lectureSizes,
  type SchoolStats,
} from "$lib/school-stats";
import { normalize } from "$lib/format";
import { madisonDate, type CampusDay } from "$lib/campus";
import campus from "../../../../.site/import/campus.json";
import type { DocumentContext } from "./types";

// This source loader runs only during document preparation or local development.
let prepared: Promise<SchoolStats> | undefined;
export async function stats(context: DocumentContext) {
  return {
    schoolStats: selectStatsTerm(
      await (prepared ??= prepare().catch((error) => {
        prepared = undefined;
        throw error;
      })),
      context.url,
    ),
  };
}
async function prepare(): Promise<SchoolStats> {
  const dataset = await status();
  const terms: SchoolStats["terms"] = {};
  const term = (id: string) => (terms[id] ??= emptySchoolTerm());
  for (const id of dataset.terms) term(id);
  const [offered, teachers, grades, courses, aliases] = await Promise.all([
    query(
      undefined,
      "SELECT term,COUNT(DISTINCT uid) count FROM offerings GROUP BY term",
    ),
    query(
      undefined,
      "SELECT term,COUNT(DISTINCT instructor_uid) count FROM teaching GROUP BY term",
    ),
    query(
      undefined,
      "SELECT term,SUM(a) a,SUM(ab) ab,SUM(b) b,SUM(bc) bc,SUM(c) c,SUM(d) d,SUM(f) f FROM grade_summaries GROUP BY term",
    ),
    query(
      undefined,
      "SELECT uid,code,title,json_extract(payload,'$.sections') sections FROM courses",
    ),
    query(undefined, "SELECT alias,uid FROM aliases"),
  ]);
  for (const row of offered) term(row.term).courses = row.count;
  for (const row of teachers) term(row.term).instructors = row.count;
  for (const row of grades) {
    const counts = [row.a, row.ab, row.b, row.bc, row.c, row.d, row.f];
    Object.assign(term(row.term), { grades: counts, ...gradeTotals(counts) });
  }
  const sizes = new Map<string, number[]>();
  const seen = new Set<string>();
  const sectionIndex = new Map<
    string,
    { term: string; first: string; last: string }[]
  >();
  const names = new Map<string, Set<string>>();
  for (const a of aliases) {
    const set = names.get(a.uid) ?? new Set();
    set.add(normalize(a.alias));
    names.set(a.uid, set);
  }
  for (const course of courses) {
    const enrolled = new Map<string, number>();
    const codes = names.get(course.uid) ?? new Set<string>();
    codes.add(normalize(course.code));
    for (const s of JSON.parse(course.sections ?? "[]")) {
      if (!s.term_id || !s.section_uid) continue;
      const t = term(s.term_id);
      if (s.start_date && s.end_date) {
        const first = madisonDate(new Date(s.start_date));
        const last = madisonDate(new Date(s.end_date));
        for (const code of codes) {
          const key = `${code}:${s.section_type} ${s.section_number}`;
          const records = sectionIndex.get(key) ?? [];
          records.push({ term: s.term_id, first, last });
          sectionIndex.set(key, records);
        }
      }
      const key = `${s.term_id}:${s.section_uid}`;
      if (seen.has(key)) continue;
      seen.add(key);
      t.sections++;
      if (s.section_type !== "LEC") continue;
      t.lectures++;
      if (!Number.isInteger(s.enrolled) || s.enrolled < 0) continue;
      const list = sizes.get(s.term_id) ?? [];
      list.push(s.enrolled);
      sizes.set(s.term_id, list);
      enrolled.set(s.term_id, (enrolled.get(s.term_id) ?? 0) + s.enrolled);
    }
    for (const [id, count] of enrolled)
      term(id).largest.push({
        code: course.code,
        title: course.title,
        enrolled: count,
      });
  }
  for (const [id, t] of Object.entries(terms)) {
    Object.assign(t, lectureSizes(sizes.get(id) ?? []));
    t.largest.sort(
      (a, b) => b.enrolled - a.enrolled || a.code.localeCompare(b.code),
    );
    t.largest = t.largest.slice(0, 5);
  }
  const clock = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago",
    weekday: "short",
    hour: "numeric",
    hourCycle: "h23",
  });
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const base = join(process.cwd(), ".site/import/assets", campus.assetBase);
  const files = (await readdir(base))
    .filter((name) => /^\d{4}-\d{2}-\d{2}\.json$/.test(name))
    .sort();
  const meetingsSeen = new Set<string>();
  for (const file of files) {
    const day: CampusDay = JSON.parse(await readFile(join(base, file), "utf8"));
    for (const building of day.buildings ?? [])
      for (const meeting of building.sessions ?? []) {
        const ids = new Set(
          meeting.courses.flatMap((c) =>
            (sectionIndex.get(`${normalize(c.code)}:${c.section}`) ?? [])
              .filter((s) => s.first <= day.date && s.last >= day.date)
              .map((s) => s.term),
          ),
        );
        // Ambiguous or unmatched terms do not silently contaminate a semester.
        if (ids.size !== 1) continue;
        const id = [...ids][0];
        const key = `${id}:${building.name}:${meeting.room}:${meeting.startsAt}:${meeting.endsAt}`;
        if (meetingsSeen.has(key)) continue;
        meetingsSeen.add(key);
        const schedule = term(id).schedule;
        schedule.from =
          schedule.from === null || day.date < schedule.from
            ? day.date
            : schedule.from;
        schedule.through =
          schedule.through === null || day.date > schedule.through
            ? day.date
            : schedule.through;
        schedule.meetings++;
        // Count a meeting once in every local hour it overlaps, including partial hours.
        const slots = new Set<string>();
        for (
          let time = meeting.startsAt;
          time < meeting.endsAt;
          time = (Math.floor(time / 3600000) + 1) * 3600000
        ) {
          const parts = clock.formatToParts(time);
          const d = days.indexOf(
            parts.find((p) => p.type === "weekday")!.value,
          );
          const hour = Number(parts.find((p) => p.type === "hour")!.value);
          slots.add(`${d}:${hour}`);
        }
        for (const slot of slots) {
          const [d, hour] = slot.split(":").map(Number);
          let cell = schedule.cells.find((c) => c.day === d && c.hour === hour);
          if (!cell) {
            cell = { day: d, hour, meetings: 0 };
            schedule.cells.push(cell);
          }
          cell.meetings++;
        }
        let place = schedule.buildings.find((b) => b.name === building.name);
        if (!place) {
          place = {
            name: building.name,
            latitude: building.latitude,
            longitude: building.longitude,
            meetings: 0,
            enrolledVisits: 0,
            knownMeetings: 0,
          };
          schedule.buildings.push(place);
        }
        place.meetings++;
        if (meeting.enrolled !== null) {
          place.enrolledVisits += meeting.enrolled;
          place.knownMeetings++;
        }
      }
  }
  for (const t of Object.values(terms)) {
    t.schedule.cells.sort((a, b) => a.day - b.day || a.hour - b.hour);
    t.schedule.buildings.sort(
      (a, b) =>
        b.enrolledVisits - a.enrolledVisits || a.name.localeCompare(b.name),
    );
  }
  return { selectedTerm: dataset.term, terms };
}
