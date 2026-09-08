import { describe, it, expect } from "vitest";
import {
  localTime,
  monday,
  addDays,
  placeMeetings,
  sectionName,
} from "../../src/lib/calendar";
describe("Madison calendar", () => {
  it("keeps Madison wall time correct across daylight saving changes", () => {
    expect(localTime("2026-09-23 16:00:00+00:00")).toEqual({
      date: "2026-09-23",
      minute: 660,
    });
    expect(localTime("2026-11-23 17:00:00+00:00")).toEqual({
      date: "2026-11-23",
      minute: 660,
    });
    expect(localTime("2026-09-23 01:00:00+00:00").date).toBe("2026-09-22");
  });
  it("navigates week boundaries without the browser timezone", () => {
    expect(monday("2026-09-13")).toBe("2026-09-07");
    expect(addDays("2026-12-28", 7)).toBe("2027-01-04");
    expect(sectionName("LEC 003 #20")).toBe("LEC 003");
  });
  it("places overlapping meetings side by side and reuses lanes", () => {
    const meeting = (id: string, start: string, end: string) => ({
      meeting_id: id,
      name: "LEC 001",
      starts_at: `2026-09-23 ${start}:00+00:00`,
      ends_at: `2026-09-23 ${end}:00+00:00`,
    });
    const placed = placeMeetings(
      [
        meeting("a", "16:00", "17:00"),
        meeting("b", "16:30", "17:30"),
        meeting("c", "18:00", "19:00"),
      ],
      "2026-09-23",
    );
    expect(placed.map((m) => [m.lane, m.lanes])).toEqual([
      [0, 2],
      [1, 2],
      [0, 1],
    ]);
  });
});
