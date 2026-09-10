import { describe, expect, it } from "vitest";
import { campusCount, madisonDate, madisonLight } from "../../src/lib/campus";
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
