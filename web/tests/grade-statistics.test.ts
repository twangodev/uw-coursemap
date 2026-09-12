import { expect, it } from "vitest";
import { gradeStatistics } from "../../src/lib/grade-statistics";
it("weights moments by grade counts and interpolates sample quartiles", () => {
  const result = gradeStatistics([1, 0, 0, 0, 0, 0, 1]);
  expect(result.count).toBe(2);
  expect(result.mean).toBe(2);
  expect(result.sd).toBe(2);
  expect([result.q25, result.median, result.q75]).toEqual([1, 2, 3]);
  expect(result.cdf.map((r) => r.cumulative)).toEqual([
    50, 50, 50, 50, 50, 50, 100,
  ]);
});
it("handles empty and constant distributions without inventing spread", () => {
  expect(gradeStatistics([])).toMatchObject({
    count: 0,
    mean: null,
    sd: null,
    median: null,
    cdf: [],
  });
  expect(gradeStatistics([0, 0, 1000000, 0, 0, 0, 0])).toMatchObject({
    count: 1000000,
    mean: 3,
    sd: 0,
    q25: 3,
    median: 3,
    q75: 3,
  });
});
it("matches the moments and quantiles of the expanded observations", () => {
  const counts = [5, 2, 7, 1, 3, 2, 1];
  const sample = counts
    .flatMap((count, i) => Array(count).fill([4, 3.5, 3, 2.5, 2, 1, 0][i]))
    .sort((a, b) => a - b);
  const mean = sample.reduce((s, x) => s + x, 0) / sample.length;
  const stats = gradeStatistics(counts);
  expect(stats.mean).toBeCloseTo(mean);
  expect(stats.sd).toBeCloseTo(
    Math.sqrt(sample.reduce((s, x) => s + (x - mean) ** 2, 0) / sample.length),
  );
  expect(stats.median).toBe(sample[(sample.length - 1) / 2]);
  expect(stats.cdf.at(-1)!.cumulative).toBe(100);
});
