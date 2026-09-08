<script lang="ts">
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  let { terms }: { terms: { term: string; courses: number }[] } = $props();
  let data = $derived(
    terms.map((t) => ({ term: termName(t.term), courses: t.courses })),
  );
</script>

{#if data.length > 1}<div class="chart">
    <BarChart
      {data}
      props={{ xAxis: { tickOcclusion: true, tickSpacing: 90 } }}
      x="term"
      y="courses"
      series={[{ key: "courses", label: "Courses", color: "var(--accent)" }]}
      height={220}
    />
  </div>
  <p class="mono muted">Distinct courses recorded per term</p>{/if}

<style>
  .chart {
    height: 230px;
    margin: 1rem 0;
  }
</style>
