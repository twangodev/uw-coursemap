<script lang="ts">
  import { gradeColors as colors } from "$lib/chart-theme";
  import { AreaChart, BarChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { gradeHistory, letterGrades, otherGrades } from "$lib/grade-history";
  let { grades, through = "" }: { grades: any[]; through?: string } = $props();
  let rows = $derived(gradeHistory(grades, through));
  const series = [
    ...letterGrades.map((key, i) => ({
      key: key + "Share",
      label: key.toUpperCase(),
      color: colors[i],
    })),
    { key: "nonLetterShare", label: "Other outcomes", color: "var(--muted)" },
  ];
</script>

{#if rows.length}
  <section class="history-charts" aria-label="Historical grade outcomes">
    <div class="history-row">
      <div class="history-copy">
        <h3>Grade mix over time</h3>
        <p class="muted">
          Share of all recorded outcomes, including non-letter grades.
        </p>
        <div class="mix-legend">
          {#each series as item}<span
              ><i style:background={item.color}></i>{item.label}</span
            >{/each}
        </div>
      </div>
      <div class="history-plot">
        {#if rows.length > 1}<AreaChart
            data={rows}
            x="label"
            xScale={scalePoint()}
            {series}
            seriesLayout="stack"
            height={260}
            yDomain={[0, 100]}
            legend={false}
            props={{
              xAxis: { tickOcclusion: true, tickSpacing: 90 },
              tooltip: {
                hideTotal: true,
                item: { format: (value: number) => value.toFixed(1) + "%" },
              },
            }}
          />{:else}<p class="muted">
            One term recorded; more terms are needed to show a trend.
          </p>{/if}
      </div>
    </div>
    <div class="history-row">
      <div class="history-copy">
        <h3>Recorded grades by term</h3>
        <p class="muted">Recorded outcomes across all sections.</p>
      </div>
      <div class="history-plot">
        <BarChart
          data={rows}
          x="label"
          y="total"
          series={[
            {
              key: "total",
              label: "Recorded outcomes",
              color: "var(--accent)",
            },
          ]}
          height={260}
          props={{
            bars: { radius: 2, strokeWidth: 0 },
            xAxis: { tickOcclusion: true, tickSpacing: 90 },
          }}
        />
      </div>
    </div>
  </section>
  <details class="outcomes-table">
    <summary>Grade counts & non-letter outcomes</summary>
    <div class="table-scroll">
      <table>
        <thead
          ><tr
            ><th>Term</th>{#each letterGrades as key}<th>{key.toUpperCase()}</th
              >{/each}<th>Other outcomes</th><th>Total</th></tr
          ></thead
        ><tbody
          >{#each rows as row}<tr
              ><td>{row.label}</td>{#each letterGrades as key}<td>{row[key]}</td
                >{/each}<td>{row.nonLetter}</td><td>{row.total}</td></tr
            >{/each}</tbody
        >
      </table>
    </div>
    <p class="muted">
      Other outcomes include {otherGrades
        .map((key) => key.replaceAll("_", " "))
        .join(", ")}. These records do not establish a course completion rate.
    </p>
  </details>
{/if}

<style>
  .mix-legend {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
    font-size: 11px;
    color: var(--muted);
  }
  .mix-legend span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .mix-legend i {
    width: 7px;
    height: 7px;
    border-radius: 2px;
  }
  .history-charts {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 64px;
    margin-bottom: 28px;
  }
  .history-row {
    display: grid;
    grid-template-columns: minmax(180px, 0.8fr) minmax(0, 2fr);
    gap: 48px;
    align-items: start;
  }
  .history-copy {
    max-width: 30ch;
  }
  .history-plot {
    min-width: 0;
  }
  h3 {
    font-size: 18px;
    font-weight: 500;
    margin: 0 0 8px;
  }
  .history-charts p {
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 24px;
  }
  .outcomes-table {
    margin-top: 24px;
  }
  .outcomes-table p {
    font-size: 12px;
    line-height: 1.7;
  }
  @media (max-width: 720px) {
    .history-row {
      grid-template-columns: 1fr;
      gap: 8px;
    }
    .history-copy {
      max-width: none;
    }
    .history-charts {
      grid-template-columns: 1fr;
    }
  }
</style>
