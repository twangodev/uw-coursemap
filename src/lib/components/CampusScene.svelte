<script lang="ts">
  import { weatherSchema } from "$lib/api/schemas";
  import { onMount } from "svelte";
  import Terrace from "./Terrace.svelte";
  import {
    campusDaySchema,
    campusCaption,
    campusCount,
    madisonDate,
    madisonLight,
    madisonZone,
    type CampusCoverage,
    type CampusDay,
    type Weather,
  } from "$lib/campus";
  let { coverage }: { coverage: CampusCoverage } = $props();
  let now = $state<Date | null>(null);
  let weather = $state<Weather | null>(null);
  let day = $state<CampusDay | null>(null);
  let light = $derived(now ? madisonLight(now) : null);
  let count = $derived(
    now && day && day.date === madisonDate(now) ? campusCount(day, +now) : null,
  );
  let countdown = $derived(
    now && light ? Math.max(1, Math.ceil((+light.event - +now) / 60000)) : null,
  );
  let curve = $derived.by(() => {
    if (!day?.events.length) return "";
    const first = day.events[0][0],
      last = day.events.at(-1)![0];
    let n = 0;
    const points = day.events.map(([time, starts, ends]) => {
      n += starts - ends;
      return [time, n];
    });
    const peak = Math.max(1, ...points.map((p) => p[1]));
    return points
      .map(
        ([time, value], i) =>
          `${i ? "L" : "M"}${(((time - first) / Math.max(1, last - first)) * 110).toFixed(1)},${(24 - (value / peak) * 22).toFixed(1)}`,
      )
      .join(" ");
  });
  onMount(() => {
    const controller = new AbortController();
    let loadedDate = "",
      weatherAt = 0;
    async function tick() {
      if (document.hidden) return;
      const current = new Date();
      now = current;
      const date = madisonDate(current);
      if (date !== loadedDate) {
        loadedDate = date;
        day = null;
        if (
          coverage.from &&
          coverage.through &&
          date >= coverage.from &&
          date <= coverage.through
        ) {
          try {
            const response = await fetch(`${coverage.assetBase}/${date}.json`, {
              signal: controller.signal,
            });
            const value = response.ok ? await response.json() : null;
            const parsed = campusDaySchema.safeParse(value);
            if (
              loadedDate === date &&
              parsed.success &&
              parsed.data.date === date
            )
              day = parsed.data;
          } catch {
            /* The scene remains usable without schedule data. */
          }
        }
      }
      if (+current - weatherAt >= 900000) {
        weatherAt = +current;
        try {
          const response = await fetch("/api/weather", {
            signal: controller.signal,
          });
          weather = response.ok
            ? weatherSchema.parse(await response.json())
            : null;
        } catch {
          weather = null;
        }
      }
    }
    void tick();
    const interval = setInterval(() => void tick(), 60000);
    const visible = () => void tick();
    document.addEventListener("visibilitychange", visible);
    return () => {
      controller.abort();
      clearInterval(interval);
      document.removeEventListener("visibilitychange", visible);
    };
  });
</script>

<div class="campus-scene">
  <div class="scene-clock">
    <span class="eyebrow">Meanwhile, in Madison</span>
    <div>
      <span class="time"
        >{now
          ? new Intl.DateTimeFormat("en-US", {
              timeZone: madisonZone,
              hour: "numeric",
              minute: "2-digit",
            }).format(now)
          : "Lake Mendota"}</span
      >{#if weather?.available}<a
          href={weather.sourceUrl}
          title={`${weather.description ?? "Weather"} · ${weather.source} · observed ${weather.observedAt}`}
          >{weather.temperatureF}°F</a
        >{/if}
    </div>
  </div>
  <Terrace phase={light?.phase ?? "day"} />
  <div class="sun-note">
    {#if light && countdown}{light.eventName} in {countdown >= 60
        ? `${Math.floor(countdown / 60)}h `
        : ""}{countdown % 60}m{:else}On the shore of Lake Mendota{/if}
  </div>
  <div class="scene-bottom">
    <p>{campusCaption(light?.phase ?? "day", weather)}</p>
    <div
      class="activity"
      title="Scheduled class meetings in the published dataset, not live attendance. Cross-listed meetings at the same time and location count once."
    >
      {#if count !== null}<span
          ><strong>{count.toLocaleString()}</strong> sessions scheduled now</span
        >{#if curve}<svg
            viewBox="0 0 110 26"
            aria-label="Today's scheduled class activity"
            ><path d={curve} /></svg
          >{/if}{:else}<span>Madison runs on Central time.</span>{/if}
    </div>
  </div>
</div>

<style>
  .campus-scene {
    position: relative;
    padding-top: 60px;
  }
  .scene-clock {
    position: absolute;
    top: 0;
    left: 9%;
  }
  .eyebrow {
    color: var(--muted);
    font-size: 11px;
  }
  .scene-clock > div {
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-top: 4px;
  }
  .time {
    font-size: 24px;
    letter-spacing: -0.04em;
    font-variant-numeric: tabular-nums;
  }
  .scene-clock a {
    font-size: 12px;
    color: var(--muted);
    text-decoration: none;
  }
  .sun-note {
    position: absolute;
    right: 8%;
    top: 50px;
    color: var(--muted);
    font-size: 11px;
  }
  .scene-bottom {
    margin: 0 9%;
  }
  p {
    font-size: 15px;
    margin: 0 0 12px;
  }
  .activity {
    display: flex;
    gap: 18px;
    align-items: center;
    min-height: 28px;
    font-size: 11px;
    color: var(--muted);
  }
  strong {
    color: var(--text);
    font-weight: 500;
  }
  .activity svg {
    width: 90px;
    height: 24px;
    overflow: visible;
  }
  .activity path {
    fill: none;
    stroke: var(--accent);
    stroke-width: 1.5;
    stroke-linejoin: round;
  }
</style>
