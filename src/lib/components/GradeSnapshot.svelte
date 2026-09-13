<script lang="ts">
  import { gradeColors } from "$lib/chart-theme";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { termName } from "$lib/format";
  import { BarChart } from "layerchart";
  import MetricComparison from "./MetricComparison.svelte";
  import { metricColor, type Benchmark } from "$lib/grade-benchmarks";
  let {
    grades = [],
    benchmark,
    term = "",
    group = "UW–Madison",
  }: {
    grades: any[];
    benchmark?: Benchmark | null;
    term?: string;
    group?: string;
  } = $props();
  const keys = ["a", "ab", "b", "bc", "c", "d", "f"];
  const weights = [4, 3.5, 3, 2.5, 2, 1, 0];
  let bars = $derived(
    keys.map((key) => ({
      grade: key.toUpperCase(),
      count: grades.reduce((sum, row) => sum + (row[key] || 0), 0),
    })),
  );
  let total = $derived(bars.reduce((sum, row) => sum + row.count, 0));
  let gpa = $derived(
    total
      ? bars.reduce((sum, row, i) => sum + row.count * weights[i], 0) / total
      : null,
  );
  let percentageBars = $derived(
    bars.map((bar) => ({
      ...bar,
      percentage: total ? (bar.count / total) * 100 : 0,
    })),
  );
</script>

<div class="min-w-0 bg-surface rounded-[6px] grade-snapshot py-5 px-6">
  <div class="flex items-center justify-between snapshot-heading">
    <h2 class="text-[17px] tracking-[-0.02em]">Grade history</h2>
    <a
      class="text-[23px] py-0 px-1.5"
      href="#grades"
      aria-label="Explore full grade history">↗</a
    >
  </div>
  <div class="flex items-center gap-4.5 mt-3.5 mb-0 snapshot-value mx-0">
    <strong
      class="text-[36px] font-medium tracking-[-0.06em] leading-[1.1]"
      style:color={metricColor(gpa, benchmark?.gpa)}
      ><MetricComparison
        value={gpa}
        reference={benchmark?.gpa}
        kind="gpa"
        label="Average GPA"
        {group}><AnimatedNumber value={gpa} decimals={2} /></MetricComparison
      ></strong
    ><span class="text-[13px]"
      >average GPA<br /><span class="text-[13px] muted"
        ><AnimatedNumber value={total} /> letter grades</span
      ></span
    >
  </div>
  {#if total}<div class="h-[95px] mt-2 mini-chart">
      <BarChart
        data={percentageBars}
        x="grade"
        y="percentage"
        c="grade"
        cDomain={keys.map((key) => key.toUpperCase())}
        cRange={gradeColors}
        series={[{ key: "percentage" }]}
        height={90}
        axis={false}
        grid={false}
        props={{
          bars: {
            strokeWidth: 0,
            radius: 2,
          },
        }}
      />
    </div>
    <div class="grid grid-cols-7 gap-1 mt-2 grade-percentages">
      {#each bars as bar}<div class="grid gap-1.5 text-center text-[12px]">
          <span class="text-muted">{bar.grade}</span><strong class="font-medium"
            ><AnimatedNumber
              value={(bar.count / total) * 100}
              decimals={1}
              suffix="%"
            /></strong
          >
        </div>{/each}
    </div>
  {:else}<p class="muted">No recorded grade history.</p>{/if}
  <p class="text-[12px] text-muted mt-2 snapshot-note">
    {term ? termName(term) : "All recorded terms"} ·
    <a href="#grades">compare terms & instructors</a>
  </p>
</div>

<style>
  .mini-chart :global(rect) {
    stroke: none;
  }
  .mini-chart :global(text) {
    font-size: 11px;
    fill: var(--muted);
    stroke: none;
  }
</style>
