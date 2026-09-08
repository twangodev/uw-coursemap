import { expect, it } from "vitest";
import { gradeHistory } from "../../src/lib/grade-history";
it("keeps non-letter outcomes in history and respects the selected term", () => {
  const rows = gradeHistory(
    [
      { term_id: "1264", a: 6, f: 2, incomplete: 2, total: 10 },
      { term_id: "1272", a: 20 },
    ],
    "1264",
  );
  expect(rows).toHaveLength(1);
  expect(rows[0]).toMatchObject({
    total: 10,
    letters: 8,
    nonLetter: 2,
    aShare: 60,
    fShare: 20,
    nonLetterShare: 20,
  });
});
it("uses counts rather than adding overlapping total fields", () => {
  const [row] = gradeHistory([
    { term_id: "1264", a: 5, total: 6, incomplete: 1 },
    { term_id: "1264", a: 2, total: 2 },
  ]);
  expect(row.total).toBe(8);
  expect(row.a).toBe(7);
});
