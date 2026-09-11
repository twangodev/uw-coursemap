import { expect, it } from "vitest";
import {
  academicTerms,
  selectAcademics,
  subjectVolumes,
  type AcademicCourse,
} from "../../src/lib/school-academics";
import { documentAsset } from "../../src/lib/server/documents/storage";
const course = (
  code: string,
  count: number,
  subjects = ["CS"],
): AcademicCourse => ({
  code,
  title: code,
  subjects,
  count,
  gpa: 3,
  grades: [0, 0, count, 0, 0, 0, 0],
});
it("does not inflate school or subject volumes for aliases and cross-listings", () => {
  const row = {
    uid: "one",
    term: "1264",
    a: 10,
    ab: 0,
    b: 0,
    bc: 0,
    c: 0,
    d: 0,
    f: 0,
  };
  const terms = academicTerms(
    [row, row],
    [
      {
        uid: "one",
        code: "CS/ECE 1",
        title: "Test",
        subjects: ["CS", "ECE", "CS"],
      },
    ],
  );
  expect(terms["1264"]).toHaveLength(1);
  const subjects = subjectVolumes(terms["1264"]);
  expect(subjects.map((s) => s.count)).toEqual([5, 5]);
  expect(subjects.reduce((n, s) => n + s.count, 0)).toBe(10);
});
it("ranks the whole term before following a latest-term cohort and keeps missing history as gaps", () => {
  const terms = {
    "1252": [course("A", 30), course("B", 20)],
    "1254": [course("A", 50)],
    "1262": [course("B", 100), course("A", 90)],
  };
  const selected = selectAcademics(terms, "1264");
  expect(selected.term).toBe("1262");
  expect(selected.popularity[0].code).toBe("B");
  expect(selected.popularity[0].points.map((p) => p.rank)).toEqual([
    2,
    null,
    1,
  ]);
  expect(selectAcademics(terms, "1244").courses).toEqual([]);
  expect(selectAcademics(terms, "1252").courses).toHaveLength(2);
});
it("uses bounded static filenames for each historical term without interpreting arbitrary queries as filenames", () => {
  expect(documentAsset("/stats?term=1264")).toBe(
    "/__documents/statistics/1264.json",
  );
  expect(documentAsset("/stats?utm_source=abc")).toBe(
    "/__documents/pages/stats.json",
  );
  expect(() => documentAsset("/stats?term=../../foo")).toThrow();
  expect(() => documentAsset("/stats?term=")).toThrow();
});
