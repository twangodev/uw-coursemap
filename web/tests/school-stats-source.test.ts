import { expect, it, vi } from "vitest";
const fixtures = vi.hoisted(() => {
  const sections = [
    {
      term_id: "1272",
      section_uid: "s1",
      section_type: "LEC",
      section_number: "001",
      enrolled: 20,
      start_date: "2026-09-01T00:00:00Z",
      end_date: "2026-12-20T00:00:00Z",
    },
    {
      term_id: "1272",
      section_uid: "s2",
      section_type: "DIS",
      section_number: "301",
      enrolled: 10,
    },
    {
      term_id: "1272",
      section_uid: "s3",
      section_type: "LEC",
      section_number: "002",
      enrolled: null,
    },
  ];
  const meeting = {
    startsAt: Date.parse("2026-09-08T13:30:00Z"),
    endsAt: Date.parse("2026-09-08T14:20:00Z"),
    room: "101",
    enrolled: 20,
    courses: [
      { code: "CS 300", section: "LEC 001" },
      { code: "COMPSCI 300", section: "LEC 001" },
    ],
    instructors: [],
  };
  return {
    sections,
    meeting,
    coverage: { from: "2026-09-08" as string | null, assetBase: "/campus" },
  };
});
vi.mock("$lib/server/data", () => ({
  status: async () => ({ term: "1272", terms: ["1272", "1264"] }),
  query: async (_: unknown, sql: string) => {
    if (sql.includes("FROM offerings")) return [{ term: "1272", count: 1 }];
    if (sql.includes("FROM teaching")) return [{ term: "1272", count: 1 }];
    if (sql.includes("FROM grade_summaries"))
      return [{ term: "1264", a: 10, ab: 0, b: 0, bc: 0, c: 0, d: 0, f: 0 }];
    if (sql.includes("FROM courses"))
      return [
        {
          uid: "c1",
          code: "COMPSCI 300",
          title: "Programming II",
          sections: JSON.stringify(fixtures.sections),
        },
        {
          uid: "c1",
          code: "CS 300",
          title: "Programming II",
          sections: JSON.stringify(fixtures.sections),
        },
      ];
    return [{ alias: "CS300", uid: "c1" }];
  },
}));
vi.mock("../../.site/import/campus.json", () => ({
  default: fixtures.coverage,
}));
vi.mock("node:fs/promises", () => ({
  readdir: vi.fn(async () => ["2026-09-08.json", "2026-11-01.json"]),
  readFile: async (path: string) =>
    JSON.stringify({
      date: path.endsWith("2026-11-01.json") ? "2026-11-01" : "2026-09-08",
      buildings: [
        {
          name: "Test Hall",
          latitude: 43.07,
          longitude: -89.4,
          sessions: path.endsWith("2026-11-01.json")
            ? [
                {
                  ...fixtures.meeting,
                  startsAt: Date.parse("2026-11-01T06:30:00Z"),
                  endsAt: Date.parse("2026-11-01T07:30:00Z"),
                },
              ]
            : [
                fixtures.meeting,
                fixtures.meeting,
                {
                  ...fixtures.meeting,
                  startsAt: fixtures.meeting.startsAt + 86400000,
                  endsAt: fixtures.meeting.endsAt + 86400000,
                  courses: [{ code: "UNKNOWN 1", section: "LEC 001" }],
                },
              ],
        },
      ],
    }),
}));
import { stats } from "../../src/lib/server/documents/stats";
it("deduplicates cross-listed sections and meetings while retaining explicit enrollment coverage", async () => {
  const { schoolStats } = await stats({
    url: new URL("https://example.com/stats"),
    params: {},
    setHeaders: () => {},
  });
  const term = schoolStats.terms["1272"];
  expect(term.sections).toBe(3);
  expect(term.lectures).toBe(2);
  expect(term.knownLectures).toBe(1);
  expect(term.medianLecture).toBe(20);
  expect(term.largest).toHaveLength(1);
  expect(term.largest[0].enrolled).toBe(20);
  expect(term.schedule.meetings).toBe(2);
  expect(term.schedule.cells).toEqual([
    { day: 1, hour: 8, meetings: 1 },
    { day: 1, hour: 9, meetings: 1 },
    { day: 6, hour: 1, meetings: 1 },
  ]);
  expect(term.schedule.buildings[0].enrolledVisits).toBe(40);
  expect(schoolStats.terms["1264"].schedule.meetings).toBe(0);
  expect(schoolStats.terms["1264"].gpa).toBe(4);
});

it("keeps grades usable when the publication contains no schedule assets", async () => {
  vi.resetModules();
  fixtures.coverage.from = null;
  const { readdir } = await import("node:fs/promises");
  vi.mocked(readdir).mockClear();
  const { stats: load } = await import("../../src/lib/server/documents/stats");
  const { schoolStats } = await load({
    url: new URL("https://example.com/stats"),
    params: {},
    setHeaders: () => {},
  });
  expect(schoolStats.terms["1264"].gpa).toBe(4);
  expect(schoolStats.terms["1272"].schedule.meetings).toBe(0);
  expect(readdir).not.toHaveBeenCalled();
});
