import { expect, it } from "vitest";
import { courseFit } from "../../src/lib/course-fit";

it("describes grade outcomes with stable thresholds and no personal prediction", () => {
  expect(courseFit({ gpa: 3.5, reference: 3.3, group: "COMPSCI" })).toContain("higher grades");
  expect(courseFit({ gpa: 3.1, reference: 3.3, group: "COMPSCI" })).toContain("run lower");
  expect(courseFit({ gpa: 3.4, reference: 3.3, group: "COMPSCI" })).toContain("close to the average");
  expect(courseFit({ gpa: 3.4, reference: null, group: "COMPSCI" })).toBe("");
});
it("keeps lecture and discussion sizes separate and ignores empty or duplicated sections", () => {
  const sections = [
    { section_uid: "a", section_type: "LEC", enrolled: 150 },
    { section_uid: "a", section_type: "LEC", enrolled: 150 },
    { section_uid: "b", section_type: "LEC", enrolled: 250 },
    { section_uid: "c", section_type: "DIS", enrolled: 20 },
    { section_uid: "d", section_type: "DIS", enrolled: null },
    { section_uid: "e", section_type: "DIS", enrolled: 0 },
  ];
  const text = courseFit({ group: "school", sections });
  expect(text).toContain("Lectures are large, with a median of 200");
  expect(text).toContain("Discussion sections are small, with a median of 20");
});
it("omits unsupported claims and uses middle-sized section wording", () => {
  expect(courseFit({ group: "school" })).toBe("");
  expect(courseFit({ group: "school", sections: [{ section_type: "LAB", enrolled: 40 }] })).toContain("Labs are mid-sized");
});
