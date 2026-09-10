<script lang="ts">
  import { weatherSchema } from "$lib/api/schemas";
  import { onMount } from "svelte";
  import { Tooltip } from "bits-ui";
  import { Info } from "@lucide/svelte";
  import CampusFactValue from "./CampusFactValue.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import {
    campusDaySchema,
    campusFacts,
    madisonDate,
    madisonZone,
    type CampusCoverage,
    type CampusDay,
    type Weather,
  } from "$lib/campus";
  let {
    coverage,
    onactivity,
  }: {
    coverage: CampusCoverage;
    onactivity?: (day: CampusDay | null, now: number) => void;
  } = $props();
  let now = $state<Date | null>(null);
  let weather = $state<Weather | null>(null);
  let day = $state<CampusDay | null>(null);
  let index = $state(0);
  let infoOpen = $state(false);
  let interacting = $state(false);
  let focused = $state(false);
  let reducedMotion = $state(false);
  let facts = $derived(now ? campusFacts(day, now, weather) : []);
  let students = $derived(facts.find((f) => f.id === "students"));
  let fact = $derived(facts[index % Math.max(1, facts.length)]);
  $effect(() => {
    if (now) onactivity?.(day, +now);
  });
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
  <div class="scene-header">
    <span>Meanwhile, in Madison</span>
    <div class="live-context">
      {#if students}<span class="live-students" title={students.detail}
          ><i></i>≈ <AnimatedNumber value={Number(students.value)} /> students scheduled
          now</span
        >{/if}
      <time
        >{now
          ? new Intl.DateTimeFormat("en-US", {
              timeZone: madisonZone,
              hour: "numeric",
              minute: "2-digit",
            }).format(now)
          : "Central time"}</time
      >
    </div>
  </div>
  <div class="fact-stage" aria-live="off">
    <div class="fact">
      {#if fact}
        <span class="qualifier">{fact.prefix ?? "\u00a0"}</span>
        <div class="fact-value">
          <CampusFactValue {fact} />
        </div>
        <p>
          {fact.label}

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
        </p>
      {:else}
        <span class="qualifier">Between lakes. Between classes.</span>
        <div class="fact-value welcome">Campus,<br />in motion.</div>
      {/if}
    </div>
  </div>
</section>

<style>
  .campus-scene {
    pointer-events: none;
    z-index: 1;
    position: relative;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    isolation: isolate;
    padding: 0;
  }
  .fact-value,
  .qualifier,
  .fact p,
  .scene-header {
    width: fit-content;
    pointer-events: auto;
  }
  .scene-header {
    width: 100%;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 11px;
    color: var(--muted);
  }
  .live-context {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px 18px;
  }
  .live-students {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
  }
  .live-students i {
    width: 5px;
    height: 5px;
    background: var(--accent);
    border-radius: 50%;
    margin-right: 3px;
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
    min-height: 270px;
  }
  .fact {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
    justify-content: center;
  }
  .qualifier {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .fact-value {
    font-size: clamp(60px, 7vw, 96px);
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
    max-width: 460px;
    margin: 15px 0 12px;
    text-wrap: balance;
  }
  :global(.campus-fact-info) {
    pointer-events: auto;
    display: inline-flex;
    vertical-align: middle;
    margin-left: 5px;
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
  @media (max-width: 700px) {
    .fact-value,
    .qualifier,
    .fact p,
    .scene-header {
      width: fit-content;
      pointer-events: auto;
    }
    .scene-header {
      width: 100%;
      flex-wrap: wrap;
    }
    .live-context {
      width: 100%;
      justify-content: space-between;
    }

    .campus-scene {
      pointer-events: none;
      z-index: 1;
      min-height: 275px;
      padding: 0;
    }
    .fact-stage {
      min-height: 235px;
    }
    .fact-value {
      font-size: 60px;
    }
    p {
      max-width: 300px;
    }
  }
</style>
