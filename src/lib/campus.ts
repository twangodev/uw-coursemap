import { z } from "zod";
import { getTimes } from "suncalc";
export interface Weather {
  available: boolean;
  temperatureF: number | null;
  description: string | null;
  observedAt: string | null;
  source: string;
  sourceUrl: string;
}
export interface CampusCoverage {
  timezone: "America/Chicago";
  from: string | null;
  through: string | null;
  assetBase: string;
}
export const campusDaySchema = z.object({
  date: z.string(),
  events: z.array(
    z.tuple([
      z.number().finite(),
      z.number().int().nonnegative(),
      z.number().int().nonnegative(),
    ]),
  ),
});
export type CampusDay = z.infer<typeof campusDaySchema>;
export const madisonZone = "America/Chicago";
export function madisonDate(date: Date) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: madisonZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const value = (type: string) => parts.find((p) => p.type === type)!.value;
  return `${value("year")}-${value("month")}-${value("day")}`;
}
export function campusCount(day: CampusDay, now: number) {
  let count = 0;
  for (const [at, starts, ends] of day.events) {
    if (at > now) break;
    count += starts - ends;
  }
  return Math.max(0, count);
}
export function madisonLight(now: Date) {
  // Noon UTC falls on the same Madison calendar date, independent of visitor timezone.
  const day = new Date(madisonDate(now) + "T18:00:00Z");
  const sun = getTimes(day, 43.0766, -89.4);
  if (
    !sun.dawn ||
    !sun.dusk ||
    !sun.sunriseEnd ||
    !sun.goldenHour ||
    !sun.sunrise ||
    !sun.sunset
  )
    return null;
  const phase =
    now < sun.dawn || now >= sun.dusk
      ? "night"
      : now < sun.sunriseEnd
        ? "dawn"
        : now >= sun.goldenHour
          ? "sunset"
          : "day";
  const nextSunrise = getTimes(
    new Date(+day + 86400000),
    43.0766,
    -89.4,
  ).sunrise;
  if (!nextSunrise) return null;
  const event =
    now < sun.sunrise
      ? sun.sunrise
      : now < sun.sunset
        ? sun.sunset
        : nextSunrise;
  return {
    phase,
    event,
    eventName: now >= sun.sunrise && now < sun.sunset ? "Sunset" : "Sunrise",
  };
}
export function campusCaption(phase: string, weather: Weather | null) {
  if (
    weather?.available &&
    weather.temperatureF !== null &&
    weather.temperatureF < 50
  )
    return "Bring a layer for the lake.";
  if (
    weather?.available &&
    /rain|snow|storm|drizzle/i.test(weather.description || "")
  )
    return "A good day for a window seat.";
  if (phase === "night") return "A little quieter by the lake.";
  if (phase === "dawn") return "A new day on the Isthmus.";
  if (
    phase === "sunset" &&
    weather?.available &&
    weather.temperatureF! >= 60 &&
    /clear|fair|sunny/i.test(weather.description || "")
  )
    return "A good evening for the Terrace.";
  if (phase === "sunset") return "The day is winding down.";
  return "Madison, between classes.";
}
