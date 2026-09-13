<script lang="ts">
  import { weatherSchema } from "$lib/api/schemas";
  import { fade, fly } from "svelte/transition";
  import { onMount } from "svelte";
  import InfoTooltip from "./InfoTooltip.svelte";
  import CampusFactValue from "./CampusFactValue.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import {
    campusDaySchema,
    campusFacts,
    madisonDate,
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
  let introElapsed = $state(false);
  let scheduleReady = $state(false);
  let infoOpen = $state(false);
  let interacting = $state(false);
  let focused = $state(false);
  let reducedMotion = $state(false);
  let facts = $derived(now ? campusFacts(day, now, weather) : []);
  let showStats = $derived(introElapsed && scheduleReady && facts.length > 0);
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
      scheduleReady = true;
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
    const introTimer = setTimeout(() => {
      introElapsed = true;
    }, 1600);
    void tick();
    const interval = setInterval(() => void tick(), 60000);
    const rotate = setInterval(() => {
      if (
        showStats &&
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
      clearTimeout(introTimer);
      clearInterval(interval);
      clearInterval(rotate);
      document.removeEventListener("visibilitychange", visible);
      motion.removeEventListener("change", updateMotion);
    };
  });
</script>

<section
  class="pointer-events-none z-1 relative min-h-75 flex flex-col isolate p-0 campus-scene"
  aria-label="Campus activity"
  onpointerenter={() => (interacting = true)}
  onpointerleave={() => (interacting = false)}
  onfocusin={() => (focused = true)}
  onfocusout={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node))
      focused = false;
  }}
>
  <div
    class="min-h-4 w-full pointer-events-auto flex justify-end gap-3 text-[11px] text-muted scene-header"
  >
    <div
      class="flex items-center justify-end flex-wrap gap-y-2 gap-x-4.5 live-context"
    >
      {#if students}<span
          class="inline-flex items-center gap-1 text-[11px] live-students"
          title={students.detail}
          ><i class="w-[5px] h-[5px] bg-accent rounded-[50%] mr-[3px]"></i>≈ <AnimatedNumber
            value={Number(students.value)}
          /> students scheduled now</span
        >{/if}
    </div>
  </div>
  <div class="relative min-h-67.5 fact-stage" aria-live="off">
    {#if showStats && fact}
      <div
        class="absolute inset-0 flex flex-col items-start text-left justify-center fact"
        in:fly={{
          y: reducedMotion ? 0 : 4,
          duration: reducedMotion ? 0 : 420,
          delay: reducedMotion ? 0 : 120,
        }}
      >
        <span
          class="min-h-4 w-fit pointer-events-auto text-[12px] text-muted mb-2 qualifier"
          >{fact.prefix ?? "\u00a0"}</span
        >
        <div
          class="min-h-4 w-fit pointer-events-auto text-[clamp(60px,_7vw,_96px)] tracking-[-0.055em] font-medium leading-[1.08] text-foreground whitespace-nowrap fact-value"
        >
          <CampusFactValue {fact} />
        </div>
        <p
          class="text-[20px] tracking-[-0.025em] leading-[1.35] max-w-115 mt-[15px] mb-3 text-balance min-h-4 w-fit pointer-events-auto mx-0"
        >
          {fact.label}

          <InfoTooltip
            label="About this campus fact"
            bind:open={infoOpen}
            contentClass="campus-fact-tooltip">{fact.detail}</InfoTooltip
          >
        </p>
      </div>
    {:else}
      <div
        class="absolute inset-0 flex flex-col items-start text-left justify-center fact intro"
        out:fade={{ duration: reducedMotion ? 0 : 240 }}
      >
        <h2
          class="text-[clamp(48px,_5.5vw,_72px)] font-medium tracking-[-0.055em] leading-[1.06] m-0 welcome"
        >
          <span class="block">UW–Madison</span> courses
        </h2>
        <p
          class="text-[20px] tracking-[-0.025em] leading-[1.35] max-w-115 mt-[15px] mb-3 text-balance min-h-4 w-fit pointer-events-auto text-muted mx-0"
        >
          Find your next class.
        </p>
      </div>
    {/if}
  </div>
</section>

<style>
  .fact-stage {
    flex: 1;
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
