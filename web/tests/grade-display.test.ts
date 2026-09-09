import { expect, it } from "vitest";
import { gradeDisplay } from "../../src/lib/grade-display";
const grades = [
  { term_id: "1252", a: 20 },
  { term_id: "1264", a: 0 },
  { term_id: "1274", a: 10 },
  { term_id: "1262", b: 15 },
];
it("uses the latest earlier term with letter grades when a range cannot be estimated", () => {
  expect(gradeDisplay(grades, "1272", "1272", false)).toEqual({
    mode: "fallback",
    term: "1262",
  });
});
it("preserves a supported projection and explicit historical or all-time selections", () => {
  expect(gradeDisplay(grades, "1272", "1272", true).mode).toBe("projected");
  expect(gradeDisplay(grades, "1252", "1272", false)).toEqual({
    mode: "recorded",
    term: "1252",
  });
  expect(gradeDisplay(grades, "", "1272", false)).toEqual({
    mode: "recorded",
    term: "",
  });
});
it("handles missing history and instructor subsets without inventing grades", () => {
  expect(gradeDisplay([], "1272", "1272", false).mode).toBe("empty");
  expect(gradeDisplay(grades.slice(0, 1), "1272", "1272", false).term).toBe(
    "1252",
  );
});
