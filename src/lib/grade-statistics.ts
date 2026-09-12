const points = [4, 3.5, 3, 2.5, 2, 1, 0];
const labels = ["A", "AB", "B", "BC", "C", "D", "F"];

/** Descriptive statistics over letter-grade records, without expanding counts into samples. */
export function gradeStatistics(counts: readonly number[]) {
  const rows = points
    .map((score, i) => ({ score, grade: labels[i], count: counts[i] ?? 0 }))
    .reverse();
  const count = rows.reduce((sum, row) => sum + row.count, 0);
  const mean = count
    ? rows.reduce((sum, row) => sum + row.score * row.count, 0) / count
    : null;
  const sd =
    mean === null
      ? null
      : Math.sqrt(
          rows.reduce(
            (sum, row) => sum + row.count * (row.score - mean) ** 2,
            0,
          ) / count,
        );
  function at(index: number) {
    let cumulative = 0;
    for (const row of rows) {
      cumulative += row.count;
      if (index < cumulative) return row.score;
    }
    return rows.at(-1)!.score;
  }
  // Type-7 sample quantiles: linear interpolation between adjacent order statistics.
  function quantile(q: number) {
    if (!count) return null;
    const rank = (count - 1) * q;
    const lower = Math.floor(rank);
    return at(lower) + (at(Math.ceil(rank)) - at(lower)) * (rank - lower);
  }
  let cumulative = 0;
  const cdf = count
    ? rows.map((row) => {
        cumulative += row.count;
        return {
          ...row,
          cumulative: (cumulative / count) * 100,
          percentage: (row.count / count) * 100,
        };
      })
    : [];
  return {
    count,
    mean,
    sd,
    q25: quantile(0.25),
    median: quantile(0.5),
    q75: quantile(0.75),
    cdf,
  };
}
