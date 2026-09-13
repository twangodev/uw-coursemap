<script lang="ts">
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { termName } from "$lib/format";
  import type { GradeProjection } from "$lib/grade-projection";
  let {
    projection,
    term,
  }: { projection?: GradeProjection | null; term: string } = $props();
</script>

<div class="grade-estimate">
  <div class="grid gap-1.5 mb-5 projection-heading">
    <h3 class="text-[16px] m-0 font-medium">{termName(term)} · Projected</h3>
    <span class="text-[12px] muted">Before grades are released</span>
  </div>
  {#if projection?.interval}
    <p class="text-[40px] tracking-[-0.04em] leading-[1.3] projected-range">
      <AnimatedNumber
        value={projection.interval.lower}
        decimals={2}
      />–<AnimatedNumber value={projection.interval.upper} decimals={2} />
      <span class="text-[14px] tracking-[0] text-muted">average GPA</span>
    </p>
    <p class="text-muted text-[13px] mt-2 interval-label">
      Approximate {projection.interval.coverage}% prediction interval
    </p>
    <div
      class="relative h-1 bg-border mt-7 rounded-[2px] interval-scale"
      aria-hidden="true"
    >
      <div
        class="absolute top-[-3px] h-2.5 min-w-0.5 rounded-[3px] bg-foreground interval-band"
        style:left={`${(projection.interval.lower / 4) * 100}%`}
        style:width={`${((projection.interval.upper - projection.interval.lower) / 4) * 100}%`}
      ></div>
    </div>
    <div
      class="flex justify-between text-[11px] text-muted mt-2 scale-labels"
      aria-hidden="true"
    >
      <span>0.0</span><span>4.0</span>
    </div>
  {:else}
    <p class="muted">
      Not enough historical forecasts to estimate a reliable range.
    </p>
  {/if}
  {#if projection}<details class="pb-0 mt-5 text-[12px]">
      <summary>About this estimate</summary>
      <p class="leading-[1.7] mt-3">
        The course’s semester-average GPA, not an individual student’s grade.
        The center uses {projection.sourceTerms.length}
        {projection.sameSeason ? "same-season" : "recent"} terms, weighted toward
        recent results.
      </p>
      <p class="leading-[1.7] mt-3">
        The range uses the finite-sample 80th-percentile rank of absolute errors
        from earlier same-season forecasts. Each forecast uses only records from
        earlier terms. At least four forecasts are required; bounds are rounded
        outward and limited to 0–4. This is an empirical estimate: changing
        instructors or grading policies can reduce its coverage.
      </p>
      {#if projection.backtest}<p class="leading-[1.7] mt-3">
          {projection.backtest.terms} earlier forecasts · {projection.backtest.gpaError.toFixed(
            2,
          )} GPA average error.
        </p>{/if}
    </details>{/if}
</div>
