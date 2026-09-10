import { z } from "zod";
import type { Weather } from "$lib/campus";

export async function madisonWeather(
  fetcher: typeof fetch = fetch,
  now = Date.now(),
): Promise<Weather> {
  const unavailable: Weather = {
    available: false,
    temperatureF: null,
    description: null,
    observedAt: null,
    source: "National Weather Service · KMSN",
    sourceUrl: "https://www.weather.gov/wrh/timeseries?site=KMSN",
  };
  try {
    const response = await fetcher(
      "https://api.weather.gov/stations/KMSN/observations/latest",
      {
        headers: {
          "User-Agent": "uwcourses (https://uwcourses.com)",
          Accept: "application/geo+json",
        },
        signal: AbortSignal.timeout(5000),
      },
    );
    if (!response.ok) return unavailable;
    const { properties } = z
      .object({
        properties: z.object({
          timestamp: z.string(),
          temperature: z.object({
            value: z.number().finite(),
            unitCode: z.literal("wmoUnit:degC"),
          }),
          textDescription: z.string().nullable().optional(),
        }),
      })
      .parse(await response.json());
    const age = now - Date.parse(properties.timestamp);
    const temperature = properties.temperature?.value;
    if (
      !Number.isFinite(age) ||
      age > 7200000 ||
      age < -300000 ||
      typeof temperature !== "number" ||
      !Number.isFinite(temperature)
    )
      return unavailable;
    if (properties.temperature.unitCode !== "wmoUnit:degC") return unavailable;
    return {
      ...unavailable,
      available: true,
      temperatureF: Math.round((temperature * 9) / 5 + 32),
      description:
        typeof properties.textDescription === "string"
          ? properties.textDescription
          : null,
      observedAt: properties.timestamp,
    };
  } catch {
    return unavailable;
  }
}
