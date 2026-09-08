import { expect, it } from "vitest";
import { citationKey, citationNumbers } from "../../src/lib/citations";
it("reuses source numbers across claims while keeping grade sections distinct", () => {
  const review = { type: "review", source_review_id: "review-1" };
  const grade = { type: "grade", course_id: "COMPSCI 300", term_id: "1264", section_number: 1 };
  const other = { ...grade, section_number: 2 };
  const map = citationNumbers({ quick_take: [{ citations: [review, grade] }], instructors: [{ summary: [{ citations: [review, other] }] }] });
  expect(map.size).toBe(3);
  expect(map.get(citationKey(review))).toBe(1);
  expect(map.get(citationKey(grade))).toBe(2);
  expect(map.get(citationKey(other))).toBe(3);
});
