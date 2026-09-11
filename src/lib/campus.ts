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
  maxConcurrentClasses: number;
}
const buildingSchema = z.object({
  sessions: z
    .array(
      z.object({
        startsAt: z.number().finite(),
        endsAt: z.number().finite(),
        room: z.string(),
        enrolled: z.number().int().nonnegative().nullable(),
        courses: z.array(z.object({ code: z.string(), section: z.string() })),
        instructors: z.array(z.string()),
      }),
    )
    .optional(),
  name: z.string(),
  latitude: z.number().finite().min(-90).max(90),
  longitude: z.number().finite().min(-180).max(180),
  events: z.array(
    z.tuple([
      z.number().finite(),
      z.number().int().nonnegative(),
      z.number().int().nonnegative(),
    ]),
  ),
});
export const campusDaySchema = z.object({
  buildings: z.array(buildingSchema).optional(),
  date: z.string(),
  enrollmentEvents: z
    .array(
      z.tuple([
        z.number().finite(),
        z.number().int().nonnegative(),
        z.number().int().nonnegative(),
        z.number().int().nonnegative(),
        z.number().int().nonnegative(),
      ]),
    )
    .optional(),
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
export interface CampusFact {
  at?: number;
  id: string;
  value: number | string;
  label: string;
  detail: string;
  prefix?: string;
  suffix?: string;
}
export function campusFacts(
  day: CampusDay | null,
  now: Date,
  weather: Weather | null,
): CampusFact[] {
  const facts: CampusFact[] = [];
  const time = (at: number) =>
    new Intl.DateTimeFormat("en-US", {
      timeZone: madisonZone,
      hour: "numeric",
      minute: "2-digit",
    }).format(at);
  if (day?.date === madisonDate(now)) {
    const count = campusCount(day, +now);
    let seats = 0,
      covered = 0;
    for (const [
      at,
      starts,
      ends,
      knownStarts,
      knownEnds,
    ] of day.enrollmentEvents ?? []) {
      if (at > +now) break;
      seats += starts - ends;
      covered += knownStarts - knownEnds;
    }
    if (count > 0 && covered / count >= 0.9 && seats > 0) {
      const precision = seats >= 1000 ? 50 : 10;
      facts.push({
        id: "students",
        value: Math.max(1, Math.round(seats / precision) * precision),
        prefix: "About",
        label: "students scheduled in class right now",
        detail:
          "Estimated from published section enrollments, not live attendance or unique students. Cross-listed copies of the same section count once. At least 90% of active meetings have matched enrollment; missing meetings are not extrapolated.",
      });
    }
    facts.push({
      id: "now",
      value: count,
      label:
        count === 1
          ? "class in session right now"
          : "classes in session right now",
      detail:
        "Published class schedules, not live attendance. Meetings at the same time and room count once.",
    });
    const soon = day.events
      .filter(([at]) => at > +now && at <= +now + 15 * 60000)
      .reduce((sum, [, starts]) => sum + starts, 0);
    if (soon)
      facts.push({
        id: "soon",
        value: soon,
        label:
          soon === 1
            ? "class starts in the next 15 minutes"
            : "classes start in the next 15 minutes",
        detail: "Based on today's published meeting schedule, in Madison time.",
      });
    const total = day.events.reduce((sum, [, starts]) => sum + starts, 0);
    facts.push({
      id: "today",
      value: total,
      label: "class meetings on the calendar today",
      detail:
        "Scheduled meetings, including lectures, discussions and labs. Not a count of unique courses or students.",
    });
    let active = 0,
      peak = 0,
      peakAt = 0;
    for (const [at, starts, ends] of day.events) {
      active += starts - ends;
      if (active > peak) {
        peak = active;
        peakAt = at;
      }
    }
    if (peak)
      facts.push({
        id: "peak",
        value: time(peakAt),
        at: peakAt,
        label: "today’s busiest moment on the timetable",
        detail: `${peak.toLocaleString()} class meetings scheduled simultaneously. Earliest time is shown if tied.`,
      });
  }
  const light = madisonLight(now);
  if (light)
    facts.push({
      id: "sun",
      value: time(+light.event),
      at: +light.event,
      label:
        light.eventName === "Sunset"
          ? "sunset over Madison. See you by the lake."
          : "sunrise over Madison. A fresh start.",
      detail: "Calculated for the UW–Madison campus coordinates.",
    });
  if (weather?.available && weather.temperatureF !== null)
    facts.push({
      id: "weather",
      value: weather.temperatureF,
      suffix: "°",
      label: "outside in Madison right now",
      detail: `${weather.description ?? "Temperature"} · Fahrenheit · ${weather.source} · observed ${weather.observedAt}`,
    });
  return facts;
}

// Same geographic bounds and linear projection as campus-map.svg.
export function campusHeat(
  day: CampusDay | null,
  now: number,
  includeIdle = false,
) {
  if (!day || day.date !== madisonDate(new Date(now))) return [];
  return (day.buildings ?? []).flatMap((building) => {
    const x = ((building.longitude + 89.425) / 0.034) * 900;
    const y = ((43.082 - building.latitude) / 0.014) * 505;
    if (x < 0 || x > 900 || y < 0 || y > 505) return [];
    let count = 0;
    for (const [at, starts, ends] of building.events) {
      if (at > now) break;
      count += starts - ends;
    }
    return count > 0 || includeIdle
      ? [{ name: building.name, x, y, count: Math.max(0, count) }]
      : [];
  });
}

/** Shared by the building colors and legend; the reference never changes with the clock. */
export function campusIntensity(count: number, maximum: number) {
  return Math.sqrt(Math.max(0, Math.min(1, count / Math.max(1, maximum))));
}
