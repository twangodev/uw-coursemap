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
  <section
    class="grid grid-cols-[minmax(0,_1fr)] gap-16 mb-7 history-charts"
    aria-label="Historical grade outcomes"
  >
    <div
      class="grid grid-cols-[minmax(180px,_0.8fr)_minmax(0,_2fr)] gap-12 items-start history-row"
    >
      <div class="max-w-[30ch] history-copy">
        <h3 class="text-[18px] font-medium mt-0 mb-2 mx-0">
          Grade mix over time
        </h3>
        <p class="text-[13px] leading-[1.6] mb-6 muted">
          Share of all recorded outcomes, including non-letter grades.
        </p>
        <div
          class="flex gap-3 flex-wrap mb-4 text-[11px] text-muted mix-legend"
        >
          {#each series as item}<span class="inline-flex items-center gap-[5px]"
              ><i
                class="w-[7px] h-[7px] rounded-[2px]"
                style:background={item.color}
              ></i>{item.label}</span
            >{/each}
        </div>
      </div>
      <div class="min-w-0 history-plot">
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
          />{:else}<p class="text-[13px] leading-[1.6] mb-6 muted">
            One term recorded; more terms are needed to show a trend.
          </p>{/if}
      </div>
    </div>
    <div
      class="grid grid-cols-[minmax(180px,_0.8fr)_minmax(0,_2fr)] gap-12 items-start history-row"
    >
      <div class="max-w-[30ch] history-copy">
        <h3 class="text-[18px] font-medium mt-0 mb-2 mx-0">
          Recorded grades by term
        </h3>
        <p class="text-[13px] leading-[1.6] mb-6 muted">
          Recorded outcomes across all sections.
        </p>
      </div>
      <div class="min-w-0 history-plot">
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
  <details class="mt-6 outcomes-table">
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
    <p class="text-[12px] leading-[1.7] muted">
      Other outcomes include {otherGrades
        .map((key) => key.replaceAll("_", " "))
        .join(", ")}. These records do not establish a course completion rate.
    </p>
  </details>
{/if}

<style>
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
