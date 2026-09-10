<script lang="ts">
  import { weatherSchema } from "$lib/api/schemas";
  import { onMount } from "svelte";
  import { Tooltip } from "bits-ui";
  import { fade } from "svelte/transition";
  import { ArrowRight, Info, Pause, Play } from "@lucide/svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import campusMap from "$lib/assets/campus-map.svg";
  import {
    campusDaySchema,
    campusFacts,
    madisonDate,
    madisonZone,
    type CampusCoverage,
    type CampusDay,
    type Weather,
  } from "$lib/campus";
  let { coverage }: { coverage: CampusCoverage } = $props();
  let now = $state<Date | null>(null);
  let weather = $state<Weather | null>(null);
  let day = $state<CampusDay | null>(null);
  let index = $state(0);
  let paused = $state(false);
  let infoOpen = $state(false);
  let interacting = $state(false);
  let focused = $state(false);
  let reducedMotion = $state(false);
  let facts = $derived(now ? campusFacts(day, now, weather) : []);
  let fact = $derived(facts[index % Math.max(1, facts.length)]);
  onMount(() => {
    const controller = new AbortController();
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotion = () => {
      reducedMotion = motion.matches;
    };
    updateMotion();
    motion.addEventListener("change", updateMotion);
    let loadedDate = "",
      weatherAt = 0,
      loadingDate = "";
    async function tick() {
      if (document.hidden) return;
      const current = new Date();
      now = current;
      const date = madisonDate(current);
      if (date !== loadedDate && date !== loadingDate) {
        day = null;
        if (
          coverage.from &&
          coverage.through &&
          date >= coverage.from &&
          date <= coverage.through
        ) {
          loadingDate = date;
          try {
            const response = await fetch(`${coverage.assetBase}/${date}.json`, {
              signal: controller.signal,
            });
            const parsed = campusDaySchema.safeParse(
              response.ok ? await response.json() : null,
            );
            if (
              parsed.success &&
              parsed.data.date === date &&
              now &&
              madisonDate(now) === date
            ) {
              day = parsed.data;
              loadedDate = date;
              index = 0;
            }
          } catch {
            /* Retry on the next minute; keep the clock and solar facts. */
          } finally {
            loadingDate = "";
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
    const rotate = setInterval(() => {
      if (
        !document.hidden &&
        !paused &&
        !interacting &&
        !focused &&
        !infoOpen &&
        !reducedMotion
      )
        index = (index + 1) % Math.max(1, facts.length);
    }, 8000);
    const visible = () => void tick();
    document.addEventListener("visibilitychange", visible);
    return () => {
      controller.abort();
      clearInterval(interval);
      clearInterval(rotate);
      document.removeEventListener("visibilitychange", visible);
      motion.removeEventListener("change", updateMotion);
    };
  });
</script>

<section
  class="campus-scene"
  aria-label="Meanwhile, in Madison"
  onpointerenter={() => (interacting = true)}
  onpointerleave={() => (interacting = false)}
  onfocusin={() => (focused = true)}
  onfocusout={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node))
      focused = false;
  }}
>
  <img class="campus-map" src={campusMap} alt="" width="900" height="505" />
  <div class="scene-header">
    <span>Meanwhile, in Madison</span><time
      >{now
        ? new Intl.DateTimeFormat("en-US", {
            timeZone: madisonZone,
            hour: "numeric",
            minute: "2-digit",
          }).format(now)
        : "Central time"}</time
    >
  </div>
  <div class="fact-stage" aria-live="off">
    {#key fact?.id}
      <div
        class="fact"
        in:fade={{
          duration: reducedMotion ? 0 : 300,
          delay: reducedMotion ? 0 : 120,
        }}
        out:fade={{ duration: reducedMotion ? 0 : 120 }}
      >
        {#if fact}
          <span class="qualifier">{fact.prefix ?? "\u00a0"}</span>
          <div class="fact-value">
            {#if typeof fact.value === "number"}<AnimatedNumber
                value={fact.value}
                suffix={fact.suffix}
              />{:else}{fact.value}{/if}
          </div>
          <p>{fact.label}</p>
          <Tooltip.Provider delayDuration={150}
            ><Tooltip.Root bind:open={infoOpen} disableCloseOnTriggerClick>
              <Tooltip.Trigger
                class="campus-fact-info"
                aria-label="About this campus fact"
                onclick={() => (infoOpen = true)}
                ><Info size={14} /></Tooltip.Trigger
              >
              <Tooltip.Portal
                ><Tooltip.Content
                  class="campus-fact-tooltip"
                  role="tooltip"
                  sideOffset={6}
                  collisionPadding={12}>{fact.detail}</Tooltip.Content
                ></Tooltip.Portal
              >
            </Tooltip.Root></Tooltip.Provider
          >
        {:else}
          <span class="qualifier">Between lakes. Between classes.</span>
          <div class="fact-value welcome">Campus,<br />in motion.</div>
        {/if}
      </div>
    {/key}
  </div>
  <div class="scene-footer">
    <div class="fact-controls">
      <button
        aria-label={paused ? "Resume campus facts" : "Pause campus facts"}
        aria-pressed={paused}
        onclick={() => (paused = !paused)}
        >{#if paused}<Play size={13} />{:else}<Pause size={13} />{/if}</button
      >
      <span class="position"
        >{facts.length ? (index % facts.length) + 1 : 1} / {facts.length ||
          1}</span
      >
      <button
        aria-label="Next campus fact"
        onclick={() => (index = (index + 1) % Math.max(1, facts.length))}
        ><ArrowRight size={16} /></button
      >
    </div>
    <a class="map-credit" href="https://www.openstreetmap.org/copyright"
      >© OpenStreetMap contributors</a
    >
  </div>
</section>

<style>
  .campus-scene {
    position: relative;
    min-height: 410px;
    display: flex;
    flex-direction: column;
    isolation: isolate;
    padding: 28px 28px 20px;
  }
  .campus-map {
    position: absolute;
    inset: -25px -65px;
    width: calc(100% + 130px);
    height: calc(100% + 50px);
    object-fit: cover;
    z-index: -1;
    opacity: 0.55;
    pointer-events: none;
    mask-image: radial-gradient(ellipse at 55% 45%, #000 8%, transparent 72%);
  }
  :global(.dark) .campus-map {
    filter: invert(1);
    opacity: 0.46;
  }
  .scene-header {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 11px;
    color: var(--muted);
  }
  .scene-header > span {
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  time {
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
  .fact-stage {
    position: relative;
    flex: 1;
    min-height: 290px;
  }
  .fact {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
  }
  .qualifier {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .fact-value {
    font-size: clamp(48px, 5.2vw, 72px);
    letter-spacing: -0.055em;
    font-weight: 500;
    line-height: 1.08;
    color: var(--text);
    white-space: nowrap;
  }
  .welcome {
    font-size: 54px;
  }
  p {
    font-size: 20px;
    letter-spacing: -0.025em;
    line-height: 1.35;
    max-width: 290px;
    margin: 15px 0 12px;
    text-wrap: balance;
  }
  :global(.campus-fact-info) {
    display: inline-flex;
    padding: 2px;
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: help;
  }
  :global(.campus-fact-tooltip) {
    z-index: 100;
    max-width: min(300px, calc(100vw - 24px));
    padding: 12px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    color: var(--text);
    font: 12px/1.6 var(--font-sans);
  }
  .scene-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
  }
  .fact-controls {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  button {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    border: 0;
    background: transparent;
    color: var(--muted);
    border-radius: 50%;
    cursor: pointer;
  }
  button:hover {
    color: var(--text);
    background: var(--border);
  }
  .position {
    min-width: 36px;
    text-align: center;
    font-size: 10px;
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }
  .map-credit {
    font-size: 9px;
    color: var(--muted);
    text-decoration: none;
  }
  @media (max-width: 700px) {
    .campus-scene {
      min-height: 340px;
      padding: 24px 10px 10px;
    }
    .fact-stage {
      min-height: 250px;
    }
    .campus-map {
      inset: 0;
      width: 100%;
      height: 100%;
    }
    .fact-value {
      font-size: 58px;
    }
  }
</style>
