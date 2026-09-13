<script lang="ts">
  import { gradeColors as gradeColors } from "$lib/chart-theme";
  import { BarChart, LineChart, AreaChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX, curveStepAfter } from "d3-shape";
  import { gradeStatistics } from "$lib/grade-statistics";
  import { gradedTerm, gradeLabels, type SchoolStats } from "$lib/school-stats";
  import { termName } from "$lib/format";
  import StatsCard from "./StatsCard.svelte";
  import Disclosure from "./Disclosure.svelte";
  import Metric from "./Metric.svelte";
  import ChartFrame from "./ChartFrame.svelte";
  import { chartAxis, percentLabel } from "$lib/chart-theme";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  let { stats, term }: { stats: SchoolStats; term: string } = $props();
  let gradeMix = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => t <= term && r.gradeCount > 0)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([t, r]) =>
        Object.assign(
          { term: termName(t) },
          ...gradeLabels.map((g, i) => ({
            [g]: (r.grades[i] / r.gradeCount) * 100,
          })),
        ),
      ),
  );

  let gradeTerm = $derived(gradedTerm(stats, term));
  let grades = $derived(gradeTerm ? stats.terms[gradeTerm] : null);
  let distribution = $derived(gradeStatistics(grades?.grades ?? []));
  let bars = $derived(
    gradeLabels.map((grade, i) => ({
      grade,
      percentage: grades?.gradeCount
        ? (grades.grades[i] / grades.gradeCount) * 100
        : 0,
    })),
  );
  let gradeDots = $derived(
    Array.from({ length: 100 }, (_, index) => {
      let cumulative = 0;
      return bars.findIndex((row) => {
        cumulative += row.percentage;
        return cumulative > index + 0.5;
      });
    }),
  );
  let trend = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => t <= term && r.gradeCount > 0)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([t, r]) => ({ term: termName(t), gpa: r.gpa })),
  );
  let domain = $derived(
    trend.length
      ? [
          Math.max(
            0,
            Math.floor((Math.min(...trend.map((r) => r.gpa!)) - 0.1) * 10) / 10,
          ),
          Math.min(
            4,
            Math.ceil((Math.max(...trend.map((r) => r.gpa!)) + 0.1) * 10) / 10,
          ),
        ]
      : [0, 4],
  );
</script>

<StatsCard title="Grades" span={4}>
  {#snippet preview()}
    <strong
      class="block text-[clamp(40px,_4.5vw,_68px)] tracking-[-0.06em] font-[450] leading-[1.05] preview-number"
      ><AnimatedNumber value={grades?.gpa} decimals={2} /></strong
    >
    <span class="block text-muted text-[12px] mt-3 preview-label"
      >μ · mean grade points · {gradeTerm
        ? termName(gradeTerm)
        : "no recorded grades"}</span
    >
    {#if grades?.gradeCount}<div class="preview-grades">
        <div
          class="grid grid-cols-[repeat(20,_1fr)] gap-1 pt-5.5 grade-dots"
          role="img"
          aria-label={bars
            .map((row) => `${row.grade}: ${row.percentage.toFixed(1)}%`)
            .join(", ")}
        >
          {#each gradeDots as grade}<span
              class="w-full aspect-square rounded-[50%] opacity-[0.9]"
              style:background={gradeColors[Math.max(0, grade)]}
              title={`${bars[Math.max(0, grade)].grade}: ${bars[Math.max(0, grade)].percentage.toFixed(1)}%`}
            ></span>{/each}
        </div>
        <div
          class="hidden gap-4 flex-wrap mt-5 text-[11px] text-muted grade-dot-key"
          aria-hidden="true"
        >
          {#each gradeLabels as label, i}<span
              class="flex items-center gap-[5px]"
              ><i
                class="w-[5px] h-[5px] rounded-[50%]"
                style:background={gradeColors[i]}
              ></i>{label}</span
            >{/each}
        </div>
      </div>{/if}
    {#if distribution.count}<span
        class="block text-muted text-[11px] mt-3.5 tabular-nums preview-math"
        >σ = {distribution.sd?.toFixed(2)} · n = {distribution.count.toLocaleString()}</span
      >{/if}
  {/snippet}
  {#if grades?.gradeCount}
    <p class="text-muted text-[13px] m-0 period">
      {termName(gradeTerm!)} · recorded letter-grade distribution
    </p>
    <div class="grid grid-cols-6 gap-5 mt-7 mb-9 distribution-metrics mx-0">
      {#each [{ label: "Mean · μ", value: distribution.mean }, { label: "Std. deviation · σ", value: distribution.sd }, { label: "25th percentile", value: distribution.q25 }, { label: "Median", value: distribution.median }, { label: "75th percentile", value: distribution.q75 }] as metric}
        <Metric {...metric} decimals={2} labelFirst />
      {/each}
      <Metric label="Grade records · n" value={distribution.count} labelFirst />
    </div>
    <div class="grid grid-cols-2 gap-8 distribution-charts">
      <ChartFrame title="Grade probabilities">
        <BarChart
          data={bars}
          x="grade"
          y="percentage"
          series={[
            {
              key: "percentage",
              label: "Share of letter grades",
              color: "var(--accent)",
            },
          ]}
          height={290}
          props={{
            bars: { strokeWidth: 0 },
            yAxis: { label: "Percent" },
            tooltip: {
              hideTotal: true,
              item: { format: percentLabel },
            },
          }}
        />
      </ChartFrame>
      <div class="grade-cdf">
        <ChartFrame title="Cumulative distribution">
          <LineChart
            data={distribution.cdf}
            x="score"
            yDomain={[0, 100]}
            xDomain={[0, 4]}
            series={[
              {
                key: "cumulative",
                label: "Grades at or below this score",
                color: "var(--positive)",
              },
            ]}
            height={290}
            props={{
              xAxis: { label: "Grade points" },
              yAxis: { label: "Percent" },
              spline: { curve: curveStepAfter },
              points: { r: 3 },
              tooltip: {
                hideTotal: true,
                item: { format: percentLabel },
              },
            }}
          />
          {#snippet note()}F(x) = P(grade points ≤ x){/snippet}
        </ChartFrame>
      </div>
    </div>
    <p class="text-muted text-[12px] leading-[1.6] coverage">
      σ describes the spread of recorded letter grades. Quartiles use linear
      interpolation between ordered grade records.
    </p>
    <details class="mt-[25px] text-[13px] disclosure">
      <summary>Grade percentages</summary>
      <div class="mt-4 max-h-80 overflow-auto grade-table">
        {#each bars as row}<div class="flex justify-between gap-5 py-2 px-0">
            <span>{row.grade}</span><span>{row.percentage.toFixed(2)}%</span>
          </div>{/each}
      </div>
    </details>
    <Disclosure
      title="Grades over time"
      description="Across recorded semesters"
    >
      <h3>How the grade mix has changed</h3>
      <AreaChart
        data={gradeMix}
        x="term"
        xScale={scalePoint()}
        series={gradeLabels.map((key, i) => ({
          key,
          label: key,
          color: gradeColors[i],
        }))}
        seriesLayout="stack"
        height={280}
        yDomain={[0, 100]}
        legend={false}
        props={{
          xAxis: chartAxis,
          tooltip: {
            hideTotal: true,
            item: { format: (value: number) => value.toFixed(1) + "%" },
          },
        }}
      />
      <div class="flex gap-4 flex-wrap text-[12px] grade-key my-3 mx-0">
        {#each gradeLabels as grade, i}<span class="flex items-center gap-1.5"
            ><i class="w-3 h-[3px]" style:background={gradeColors[i]}
            ></i>{grade}</span
          >{/each}
      </div>
      <details class="mt-[25px] text-[13px] disclosure">
        <summary>Average GPA over time</summary>
        <LineChart
          data={trend}
          x="term"
          xScale={scalePoint()}
          yDomain={domain}
          series={[{ key: "gpa", label: "School GPA", color: "var(--accent)" }]}
          height={280}
          props={{
            xAxis: chartAxis,
            spline: { curve: curveMonotoneX, strokeWidth: 1.8 },
            points: { r: 2 },
            tooltip: {
              hideTotal: true,
              item: { format: (value: number) => value.toFixed(2) },
            },
          }}
        />
      </details>
      <details class="mt-[25px] text-[13px] disclosure">
        <summary>Recorded GPA by term</summary>
        <div class="mt-4 max-h-80 overflow-auto grade-table">
          {#each [...trend].reverse() as row}<div
              class="flex justify-between gap-5 py-2 px-0"
            >
              <span>{row.term}</span><span>{row.gpa?.toFixed(2)}</span>
            </div>{/each}
        </div>
      </details>
    </Disclosure>
  {/if}
</StatsCard>

<style>
  .grade-dots > span {
    transition: transform 140ms ease;
  }
  .grade-dots > span:hover {
    transform: scale(1.22);
  }
  @media (max-width: 760px) {
    .distribution-metrics {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .distribution-charts {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 500px) {
    .distribution-metrics {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .grade-dots > span {
      transition: none;
    }
  }
</style>
