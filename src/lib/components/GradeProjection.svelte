<script lang="ts">
  import { termName } from "$lib/format";
  import type { GradeProjection } from "$lib/grade-projection";
  let { projection }: { projection: GradeProjection } = $props();
</script>

<section class="projection" aria-labelledby="projection-title">
  <div class="projection-heading">
    <h2 id="projection-title">{termName(projection.target)} outlook</h2>
    <span class="muted">Before grades are released</span>
  </div>
  {#if projection.interval}
    <p class="projected-range">{projection.interval.lower.toFixed(2)}–{projection.interval.upper.toFixed(2)} <span>average GPA</span></p>
    <p class="interval-label">Approximate {projection.interval.coverage}% prediction interval</p>
    <div class="interval-scale" aria-hidden="true">
      <div class="interval-band" style:left={`${projection.interval.lower / 4 * 100}%`} style:width={`${(projection.interval.upper - projection.interval.lower) / 4 * 100}%`}></div>
    </div>
    <div class="scale-labels" aria-hidden="true"><span>0.0</span><span>4.0</span></div>
  {:else}
    <p class="muted">Not enough historical forecasts to estimate a reliable range.</p>
  {/if}
  <details>
    <summary>About this estimate</summary>
    <p>The course’s semester-average GPA, not an individual student’s grade. The center uses {projection.sourceTerms.length} {projection.sameSeason ? "same-season" : "recent"} terms, weighted toward recent results.</p>
    <p>The range uses the finite-sample 80th-percentile rank of absolute errors from earlier same-season forecasts. Each forecast uses only records from earlier terms. At least four forecasts are required; bounds are rounded outward and limited to 0–4. This is an empirical estimate: changing instructors or grading policies can reduce its coverage.</p>
    {#if projection.backtest}<p>{projection.backtest.terms} earlier forecasts · {projection.backtest.gpaError.toFixed(2)} GPA average error.</p>{/if}
  </details>
</section>

<style>
  .projection { border-top: 1px solid var(--border); padding: 32px 0; }
  .projection-heading { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 28px; }
  h2 { font-size: 23px; margin: 0; }
  .projection-heading span { font-size: 12px; }
  .projected-range { font-size: 40px; letter-spacing: -0.04em; line-height: 1.3; }
  .projected-range span { font-size: 14px; letter-spacing: 0; color: var(--muted); }
  .interval-label { color: var(--muted); font-size: 13px; margin-top: 8px; }
  .interval-scale { position: relative; height: 4px; background: var(--border); margin-top: 28px; max-width: 420px; border-radius: 2px; }
  .interval-band { position: absolute; top: -3px; height: 10px; min-width: 2px; border-radius: 3px; background: var(--text); }
  .scale-labels { display: flex; justify-content: space-between; max-width: 420px; font-size: 11px; color: var(--muted); margin-top: 8px; }
  details { margin-top: 24px; font-size: 12px; }
  details p { max-width: 80ch; line-height: 1.7; margin-top: 12px; }
  @media (max-width: 760px) { .projection-heading { align-items: start; flex-direction: column; gap: 8px; } }
</style>
