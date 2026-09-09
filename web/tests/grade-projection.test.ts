import { describe, it, expect } from "vitest";
import { projectGrades, predictionInterval } from "../../src/lib/grade-projection";
const records = Array.from({ length: 12 }, (_, i) => ({
  term_id: String(1212 + Math.floor(i / 2) * 10 + (i % 2) * 2),
  a: 60,
  ab: 20,
  b: 20,
  bc: 0,
  c: 0,
  d: 0,
  f: 0,
}));
describe("grade projections", () => {
  it("preserves a stable grade mix, normalizes percentages, and backtests it", () => {
    const prediction = projectGrades(records, "1274")!;
    expect(prediction.gpa).toBeCloseTo(3.7);
    expect(
      prediction.grades.reduce((sum, row) => sum + row.percentage, 0),
    ).toBeCloseTo(100);
    expect(prediction.sameSeason).toBe(true);
    expect(prediction.sourceTerms.every((term) => term.endsWith("4"))).toBe(
      true,
    );
    expect(prediction.backtest?.gpaError).toBeCloseTo(0);
  });
  it("never uses observations at or after its target", () => {
    const future = [
      { ...records[0], term_id: "1274", a: 0, f: 100 },
      { ...records[0], term_id: "1284", a: 0, f: 100 },
    ];
    expect(projectGrades([...records, ...future], "1274")).toEqual(
      projectGrades(records, "1274"),
    );
  });
  it("suppresses sparse and stale histories", () => {
    expect(projectGrades(records.slice(0, 2), "1224")).toBeNull();
    expect(projectGrades(records, "1404")).toBeNull();
  });
});

it("calibrates an outward-rounded bounded interval and rejects insufficient errors", () => {
  expect(predictionInterval(3.5, [0.1, 0.2, 0.3])).toBeNull();
  expect(predictionInterval(3.5, [0.1, 0.2, 0.3, 0.6])).toEqual({ lower: 2.9, upper: 4, coverage: 80, terms: 4 });
  expect(predictionInterval(0.1, [0.1, 0.2, 0.3, 0.6])?.lower).toBe(0);
});
