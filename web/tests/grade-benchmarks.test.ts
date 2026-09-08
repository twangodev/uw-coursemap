import { describe, it, expect } from "vitest";
import { aggregateTerms, cohortBenchmarks, benchmark } from "../../src/lib/grade-benchmarks";
const rows = Array.from({ length: 10 }, (_, i) => ({ uid: String(i), term: "1264", subjects: ["CS", "ECE", "CS"], gpa: 2 + i / 10, topShare: 20 + i * 5, count: 30 + i * 10 }));
describe("grade benchmarks", () => {
  it("weights courses equally and uses the median grade count", () => {
    expect(benchmark(rows)).toEqual({ size: 10, gpa: 2.45, topShare: 42.5, count: 75 });
    expect(cohortBenchmarks(rows).CS).toEqual(cohortBenchmarks(rows).school);
    expect(cohortBenchmarks(rows).ECE?.size).toBe(10);
    expect(benchmark(rows.slice(1))).toBeNull();
  });
  it("aggregates a course across matching terms before computing cohort statistics", () => {
    const merged = aggregateTerms([rows[0], { ...rows[0], term: "1254", gpa: 4, topShare: 100, count: 90 }]);
    expect(merged).toHaveLength(1);
    expect(merged[0].gpa).toBe(3.5);
    expect(merged[0].topShare).toBe(80);
    expect(merged[0].count).toBe(120);
  });
});
