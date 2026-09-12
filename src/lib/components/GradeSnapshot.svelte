<script lang="ts">
  import { gradeColors } from "$lib/chart-theme";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { termName } from "$lib/format";
  import { BarChart } from "layerchart";
  import MetricComparison from "./MetricComparison.svelte";
  import { metricColor, type Benchmark } from "$lib/grade-benchmarks";
  let { grades = [], benchmark, term = "", group = "UW–Madison" }: { grades: any[]; benchmark?: Benchmark | null; term?: string; group?: string } = $props();
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

<div class="grade-snapshot">
  <div class="snapshot-heading">
    <h2>Grade history</h2>
    <a href="#grades" aria-label="Explore full grade history">↗</a>
  </div>
  <div class="snapshot-value">
    <strong style:color={metricColor(gpa, benchmark?.gpa)}><MetricComparison value={gpa} reference={benchmark?.gpa} kind="gpa" label="Average GPA" {group}><AnimatedNumber value={gpa} decimals={2} /></MetricComparison></strong><span
      >average GPA<br /><span class="muted"
        ><AnimatedNumber value={total} /> letter grades</span
      ></span
    >
  </div>
  {#if total}<div class="mini-chart">
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
    <div class="grade-percentages">
      {#each bars as bar}<div>
          <span>{bar.grade}</span><strong
            ><AnimatedNumber value={bar.count / total * 100} decimals={1} suffix="%" /></strong
          >
        </div>{/each}
    </div>
  {:else}<p class="muted">No recorded grade history.</p>{/if}
  <p class="snapshot-note">
    {term ? termName(term) : "All recorded terms"} · <a href="#grades">compare terms & instructors</a>
  </p>
</div>

<style>
  .grade-snapshot {
    padding: 20px 24px;
    min-width: 0;
    background: var(--surface);
    border-radius: 6px;
  }
  .snapshot-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  h2 {
    font-size: 17px;
    letter-spacing: -0.02em;
  }
  .snapshot-heading a {
    font-size: 23px;
    padding: 0 6px;
  }
  .snapshot-value {
    display: flex;
    align-items: center;
    gap: 18px;
    margin: 14px 0 0;
  }
  .snapshot-value strong {
    font-size: 36px;
    font-weight: 500;
    letter-spacing: -0.06em;
    line-height: 1.1;
  }
  .snapshot-value span {
    font-size: 13px;
  }
  .mini-chart {
    height: 95px;
    margin-top: 8px;
  }
  .mini-chart :global(rect) {
    stroke: none;
  }
  .mini-chart :global(text) {
    font-size: 11px;
    fill: var(--muted);
    stroke: none;
  }
  .snapshot-note {
    font-size: 12px;
    color: var(--muted);
    margin-top: 8px;
  }
  .grade-percentages {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 4px;
    margin-top: 8px;
  }
  .grade-percentages div {
    display: grid;
    gap: 6px;
    text-align: center;
    font-size: 12px;
  }
  .grade-percentages span {
    color: var(--muted);
  }
  .grade-percentages strong {
    font-weight: 500;
  }
</style>
