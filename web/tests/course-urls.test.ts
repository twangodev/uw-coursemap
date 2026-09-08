import { expect, it, vi } from "vitest";
vi.mock("$app/environment", () => ({ building: true, dev: true }));
import { courseSlug, courseUrl, normalize } from "../../src/lib/format";
import { query } from "../../src/lib/server/data";
it("uses readable subject-number URLs, with a single canonical cross-list path", () => {
  expect(courseSlug("COMPSCI 300")).toBe("COMPSCI_300");
  expect(courseSlug("MATH 221")).toBe("MATH_221");
  expect(courseSlug("COMPSCI/ECE/EMA/EP/ME 759")).toBe("COMPSCI_ECE_EMA_EP_ME_759");
  expect(courseUrl("A A E 101")).toBe("/courses/A_A_E_101");
  expect(normalize("COMPSCI_300")).toBe("COMPSCI300");
  expect(normalize("ece-759")).toBe("ECE759");
});
it("assigns unique slugs across the full catalog and resolves each to its stable ID", async () => {
  const courses = await query(undefined, "SELECT uid,code FROM courses");
  const aliases = await query(undefined, "SELECT uid,alias FROM aliases");
  const keys = new Set(aliases.map((row) => `${row.uid}:${row.alias}`));
  const slugs = courses.map((course) => courseSlug(course.code));
  expect(new Set(slugs).size).toBe(courses.length);
  expect(
    courses.every((course) =>
      keys.has(`${course.uid}:${normalize(courseSlug(course.code))}`),
    ),
  ).toBe(true);
});
