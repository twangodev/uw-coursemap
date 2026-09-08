<script lang="ts">
  import { BarChart } from "layerchart";
  let { grades = [] }: { grades: any[] } = $props();
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
</script>

<div class="grade-snapshot">
  <div class="snapshot-heading">
    <h2>Grade history</h2>
    <a href="#grades" aria-label="Explore full grade history">↗</a>
  </div>
  <div class="snapshot-value">
    <strong>{gpa?.toFixed(2) ?? "—"}</strong><span
      >average GPA<br /><span class="muted"
        >{total.toLocaleString()} letter grades</span
      ></span
    >
  </div>
  {#if total}<div class="mini-chart">
      <BarChart
        data={bars}
        x="grade"
        y="count"
        series={[{ key: "count", color: "var(--accent)" }]}
        height={105}
        axis="x"
        grid={false}
        props={{ bars: { strokeWidth: 0, radius: 2 } }}
      />
    </div>{:else}<p class="muted">No recorded grade history.</p>{/if}
  <p class="snapshot-note">
    All recorded terms · <a href="#grades">compare terms & instructors</a>
  </p>
</div>

<style>
  .grade-snapshot {
    padding: 26px 28px 20px;
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
    font-size: 44px;
    font-weight: 500;
    letter-spacing: -0.06em;
    line-height: 1.1;
  }
  .snapshot-value span {
    font-size: 13px;
  }
  .mini-chart {
    height: 110px;
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
</style>
