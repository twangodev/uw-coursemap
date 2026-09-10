import { describe, expect, it } from "vitest";
import {
  campusFacts,
  type CampusDay,
  campusCount,
  madisonDate,
  madisonLight,
} from "../../src/lib/campus";
import { madisonWeather } from "../../src/lib/server/weather";

describe("Madison campus clock", () => {
  it("uses Madison's date across midnight and DST", () => {
    expect(madisonDate(new Date("2026-09-10T02:00:00Z"))).toBe("2026-09-09");
    expect(madisonDate(new Date("2026-11-01T06:30:00Z"))).toBe("2026-11-01");
    expect(madisonDate(new Date("2026-11-01T07:30:00Z"))).toBe("2026-11-01");
  });
  it("ends meetings exactly at their end time", () => {
    const day = {
      date: "2026-09-09",
      events: [
        [100, 2, 0],
        [200, 1, 2],
        [300, 0, 1],
      ] as [number, number, number][],
    };
    expect(campusCount(day, 99)).toBe(0);
    expect(campusCount(day, 100)).toBe(2);
    expect(campusCount(day, 200)).toBe(1);
    expect(campusCount(day, 300)).toBe(0);
  });
  it("computes sunrise and sunset for Madison", () => {
    expect(madisonLight(new Date("2026-09-09T18:00:00Z"))?.phase).toBe("day");
    expect(madisonLight(new Date("2026-09-09T06:00:00Z"))?.phase).toBe("night");
  });
});
describe("weather observations", () => {
  const now = Date.parse("2026-09-09T18:00:00Z");
  const observation = (timestamp: string, value: number | null = 20) => ({
    properties: {
      timestamp,
      temperature: { value, unitCode: "wmoUnit:degC" },
      textDescription: "Fair",
    },
  });
  const fetcher = (value: unknown) =>
    (async () => Response.json(value)) as typeof fetch;
  it("converts fresh Celsius observations", async () => {
    expect(
      await madisonWeather(fetcher(observation("2026-09-09T17:45:00Z")), now),
    ).toMatchObject({ available: true, temperatureF: 68 });
  });
  it("does not invent weather when missing, stale or invalid", async () => {
    for (const value of [
      {},
      observation("2026-09-09T12:00:00Z"),
      observation("2026-09-10T12:00:00Z"),
      observation("2026-09-09T17:45:00Z", null),
    ]) {
      expect(await madisonWeather(fetcher(value), now)).toMatchObject({
        available: false,
        temperatureF: null,
      });
    }
  });
});

describe("rotating campus facts", () => {
  const now = new Date("2026-09-10T15:00:00Z");
  const day: CampusDay = {
    date: "2026-09-10",
    events: [
      [+now, 10, 0],
      [+now + 600000, 2, 0],
      [+now + 3600000, 0, 12],
    ],
    enrollmentEvents: [[+now, 20372, 0, 9, 0]],
  };
  it("rounds enrollment estimates and requires sufficient active coverage", () => {
    expect(
      campusFacts(day, now, null).find((f) => f.id === "students")?.value,
    ).toBe(20350);
    expect(
      campusFacts(
        { ...day, enrollmentEvents: [[+now, 20372, 0, 8, 0]] },
        now,
        null,
      ).some((f) => f.id === "students"),
    ).toBe(false);
    expect(
      campusFacts({ ...day, enrollmentEvents: undefined }, now, null).some(
        (f) => f.id === "students",
      ),
    ).toBe(false);
  });
  it("derives upcoming meetings and the earliest daily peak from event boundaries", () => {
    const facts = campusFacts(day, now, null);
    expect(facts.find((f) => f.id === "now")?.value).toBe(10);
    expect(facts.find((f) => f.id === "soon")?.value).toBe(2);
    expect(facts.find((f) => f.id === "today")?.value).toBe(12);
    expect(facts.find((f) => f.id === "peak")?.value).toBe("10:10 AM");
    expect(
      campusFacts(day, new Date(+now + 3600000), null).find(
        (f) => f.id === "now",
      )?.value,
    ).toBe(0);
  });
  it("does not reuse yesterday's schedule or fabricate attendance outside coverage", () => {
    expect(
      campusFacts(day, new Date("2026-09-11T15:00:00Z"), null).map((f) => f.id),
    ).toEqual(["sun"]);
  });
});
