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
    <strong class="preview-number"
      ><AnimatedNumber value={grades?.gpa} decimals={2} /></strong
    >
    <span class="preview-label"
      >μ · mean grade points · {gradeTerm
        ? termName(gradeTerm)
        : "no recorded grades"}</span
    >
    {#if grades?.gradeCount}<div class="preview-grades">
        <div
          class="grade-dots"
          role="img"
          aria-label={bars
            .map((row) => `${row.grade}: ${row.percentage.toFixed(1)}%`)
            .join(", ")}
        >
          {#each gradeDots as grade}<span
              style:background={gradeColors[Math.max(0, grade)]}
              title={`${bars[Math.max(0, grade)].grade}: ${bars[Math.max(0, grade)].percentage.toFixed(1)}%`}
            ></span>{/each}
        </div>
        <div class="grade-dot-key" aria-hidden="true">
          {#each gradeLabels as label, i}<span
              ><i style:background={gradeColors[i]}></i>{label}</span
            >{/each}
        </div>
      </div>{/if}
    {#if distribution.count}<span class="preview-math"
        >σ = {distribution.sd?.toFixed(2)} · n = {distribution.count.toLocaleString()}</span
      >{/if}
  {/snippet}
  {#if grades?.gradeCount}
    <p class="period">
      {termName(gradeTerm!)} · recorded letter-grade distribution
    </p>
    <div class="distribution-metrics">
      {#each [{ label: "Mean · μ", value: distribution.mean }, { label: "Std. deviation · σ", value: distribution.sd }, { label: "25th percentile", value: distribution.q25 }, { label: "Median", value: distribution.median }, { label: "75th percentile", value: distribution.q75 }] as metric}
        <Metric {...metric} decimals={2} labelFirst />
      {/each}
      <Metric label="Grade records · n" value={distribution.count} labelFirst />
    </div>
    <div class="distribution-charts">
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
    <p class="coverage">
      σ describes the spread of recorded letter grades. Quartiles use linear
      interpolation between ordered grade records.
    </p>
    <details class="disclosure">
      <summary>Grade percentages</summary>
      <div class="grade-table">
        {#each bars as row}<div>
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
      <div class="grade-key">
        {#each gradeLabels as grade, i}<span
            ><i style:background={gradeColors[i]}></i>{grade}</span
          >{/each}
      </div>
      <details class="disclosure">
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
      <details class="disclosure">
        <summary>Recorded GPA by term</summary>
        <div class="grade-table">
          {#each [...trend].reverse() as row}<div>
              <span>{row.term}</span><span>{row.gpa?.toFixed(2)}</span>
            </div>{/each}
        </div>
      </details>
    </Disclosure>
  {/if}
</StatsCard>

<style>
  .grade-key {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 12px;
    margin: 12px 0;
  }
  .grade-key span {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .grade-key i {
    width: 12px;
    height: 3px;
  }
  .coverage {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
  }
  .disclosure {
    margin-top: 25px;
    font-size: 13px;
  }

  .grade-table {
    margin-top: 16px;
    max-height: 320px;
    overflow: auto;
  }

  .grade-table > div {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    padding: 8px 0;
  }
  .grade-dots {
    display: grid;
    grid-template-columns: repeat(20, 1fr);
    gap: 7px;
    padding-top: 14px;
  }
  .grade-dots > span {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 50%;
    opacity: 0.9;
    transition: transform 140ms ease;
  }
  .grade-dots > span:hover {
    transform: scale(1.22);
  }
  .grade-dot-key {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-top: 20px;
    font-size: 11px;
    color: var(--muted);
  }
  .grade-dot-key span {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .grade-dot-key i {
    width: 5px;
    height: 5px;
    border-radius: 50%;
  }
  .preview-math {
    display: block;
    color: var(--muted);
    font-size: 11px;
    margin-top: 14px;
    font-variant-numeric: tabular-nums;
  }
  .distribution-metrics {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 20px;
    margin: 28px 0 36px;
  }

  .distribution-charts {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 32px;
  }
  .period {
    color: var(--muted);
    font-size: 13px;
    margin: 0;
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
  .preview-number {
    display: block;
    font-size: clamp(40px, 4.5vw, 68px);
    letter-spacing: -0.06em;
    font-weight: 450;
    line-height: 1.05;
  }
  .preview-label {
    display: block;
    color: var(--muted);
    font-size: 12px;
    margin-top: 12px;
  }
  .preview-grades .grade-dots {
    grid-template-columns: repeat(20, 1fr);
    gap: 4px;
    padding-top: 22px;
  }
  .preview-grades .grade-dot-key {
    display: none;
  }
  @media (prefers-reduced-motion: reduce) {
    .grade-dots > span {
      transition: none;
    }
  }
</style>
