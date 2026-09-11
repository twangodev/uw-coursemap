import { expect, it } from "vitest";
import {
  emptySchoolTerm,
  gradeTotals,
  gradedTerm,
  lectureSizes,
} from "../../src/lib/school-stats";
import { selectStatsTerm } from "../../src/lib/server/documents/stats-selection";
it("weights letter grades by counts rather than course averages", () => {
  expect(gradeTotals([1, 0, 0, 0, 0, 0, 3])).toEqual({ gradeCount: 4, gpa: 1 });
  expect(gradeTotals([0, 0, 0, 0, 0, 0, 0])).toEqual({
    gradeCount: 0,
    gpa: null,
  });
});
it("bins lecture enrollment at exact boundaries and keeps missing values out of the median", () => {
  const result = lectureSizes([
    0,
    19,
    20,
    49,
    50,
    99,
    100,
    199,
    200,
    499,
    500,
    NaN,
    -1,
  ]);
  expect(result.knownLectures).toBe(11);
  expect(result.sizes.map((b) => b.count)).toEqual([2, 2, 2, 2, 2, 1]);
  expect(result.medianLecture).toBe(99);
  expect(lectureSizes([10, 20]).medianLecture).toBe(15);
  expect(lectureSizes([]).medianLecture).toBeNull();
});
it("falls back only to earlier recorded grades and does not mutate the cached term selection", () => {
  const stats = {
    selectedTerm: "1272",
    terms: {
      "1272": emptySchoolTerm(),
      "1264": { ...emptySchoolTerm(), ...gradeTotals([10, 0, 0, 0, 0, 0, 0]) },
    },
  };
  expect(gradedTerm(stats, "1272")).toBe("1264");
  expect(gradedTerm(stats, "1252")).toBeNull();
  expect(
    selectStatsTerm(stats, new URL("https://example.com/stats?term=1264"))
      .selectedTerm,
  ).toBe("1264");
  expect(stats.selectedTerm).toBe("1272");
  expect(() =>
    selectStatsTerm(stats, new URL("https://example.com/stats?term=__proto__")),
  ).toThrow();
});

it("serves term variants from one static document without database access", async () => {
  const { readDocument } =
    await import("../../src/lib/server/documents/storage");
  const stats = {
    selectedTerm: "1272",
    terms: { "1272": emptySchoolTerm(), "1264": emptySchoolTerm() },
  };
  const paths: string[] = [];
  const platform = {
    env: {
      get DB() {
        throw new Error("Statistics must not query D1");
      },
      ASSETS: {
        fetch: async (request: Request) => {
          paths.push(new URL(request.url).pathname);
          return Response.json({
            schema_version: 1,
            title: "Statistics",
            url: "https://uwcourses.com/stats",
            dataset: {},
            data: { schoolStats: stats },
          });
        },
      },
    },
  } as unknown as App.Platform;
  const selected = await readDocument(
    new URL("https://uwcourses.com/stats?term=1264"),
    platform,
  );
  expect(
    (selected.data as { schoolStats: typeof stats }).schoolStats.selectedTerm,
  ).toBe("1264");
  const defaultDocument = await readDocument(
    new URL("https://uwcourses.com/stats"),
    platform,
  );
  expect(
    (defaultDocument.data as { schoolStats: typeof stats }).schoolStats
      .selectedTerm,
  ).toBe("1272");
  expect(paths).toEqual([
    "/__documents/pages/stats.json",
    "/__documents/pages/stats.json",
  ]);
});
