export const gradeKeys = ["a", "ab", "b", "bc", "c", "d", "f"] as const;
const weights = [4, 3.5, 3, 2.5, 2, 1, 0];
type GradeTerm = { term_id: string; [key: string]: unknown };

function observations(records: GradeTerm[]) {
  return records
    .map((record) => {
      const counts = gradeKeys.map((key) => Number(record[key]) || 0);
      const n = counts.reduce((sum, count) => sum + count, 0);
      return {
        term: record.term_id,
        n,
        shares: counts.map((count) => count / n),
      };
    })
    .filter((row) => /^1\d{2}[246]$/.test(row.term) && row.n >= 30)
    .sort((a, b) => b.term.localeCompare(a.term));
}
type Observation = ReturnType<typeof observations>[number];
function estimate(history: Observation[], target: string) {
  const recent = history.filter(
    (row) => row.term < target && Number(target) - Number(row.term) <= 50,
  );
  const seasonal = recent.filter(
    (row) => row.term.slice(-1) === target.slice(-1),
  );
  const sameSeason = seasonal.length >= 3;
  const source = (sameSeason ? seasonal : recent).slice(0, sameSeason ? 5 : 6);
  if (source.length < 3 || source.reduce((sum, row) => sum + row.n, 0) < 200)
    return null;
  const influence = source.map(
    (row, i) =>
      0.8 ** i *
      (!sameSeason && row.term.slice(-1) === target.slice(-1) ? 2 : 1),
  );
  const total = influence.reduce((sum, value) => sum + value, 0);
  const shares = gradeKeys.map(
    (_, i) =>
      source.reduce((sum, row, j) => sum + row.shares[i] * influence[j], 0) /
      total,
  );
  return {
    shares,
    sameSeason,
    source,
    gpa: shares.reduce((sum, share, i) => sum + share * weights[i], 0),
  };
}

/** Walk-forward validation uses only observations preceding each held-out term. */
export function projectGrades(records: GradeTerm[], target: string) {
  const history = observations(records).filter((row) => row.term < target);
  const prediction = estimate(history, target);
  if (!prediction) return null;
  const backtests = history
    .filter((row) => row.term.slice(-1) === target.slice(-1))
    .flatMap((actual) => {
      const prior = estimate(history, actual.term);
      if (!prior) return [];
      const actualGpa = actual.shares.reduce(
        (sum, share, i) => sum + share * weights[i],
        0,
      );
      return [
        {
          term: actual.term,
          error: Math.abs(prior.gpa - actualGpa),
          mixError:
            actual.shares.reduce(
              (sum, share, i) => sum + Math.abs(share - prior.shares[i]),
              0,
            ) / 2,
        },
      ];
    })
    .slice(0, 8);
  const sourceGpas = prediction.source.map((row) =>
    row.shares.reduce((sum, share, i) => sum + share * weights[i], 0),
  );
  return {
    target,
    gpa: prediction.gpa,
    grades: gradeKeys.map((grade, i) => ({
      grade: grade.toUpperCase(),
      percentage: prediction.shares[i] * 100,
    })),
    sourceTerms: prediction.source.map((row) => row.term),
    sourceCount: prediction.source.reduce((sum, row) => sum + row.n, 0),
    sameSeason: prediction.sameSeason,
    historicalRange: [Math.min(...sourceGpas), Math.max(...sourceGpas)],
    backtest:
      backtests.length >= 3
        ? {
            terms: backtests.length,
            gpaError:
              backtests.reduce((sum, row) => sum + row.error, 0) /
              backtests.length,
            mixError:
              (backtests.reduce((sum, row) => sum + row.mixError, 0) /
                backtests.length) *
              100,
          }
        : null,
  };
}
export type GradeProjection = NonNullable<ReturnType<typeof projectGrades>>;
