<script lang="ts">
  import { gradeDisplay } from "$lib/grade-display";
  import GradeEstimate from "./GradeEstimate.svelte";
  import type { GradeProjection } from "$lib/grade-projection";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import Select from "./Select.svelte";
  import MetricComparison from "./MetricComparison.svelte";
  import { metricColor, type Benchmarks } from "$lib/grade-benchmarks";
  import { onDestroy } from "svelte";
  import { BarChart, LineChart } from "layerchart";
  import { curveMonotoneX } from "d3-shape";
  import { instructorChartRows, gradeTrendDomain, type InstructorTrend } from "$lib/instructor-trends";
  import { scalePoint } from "d3-scale";
  import { termName, courseTitle } from "$lib/format";
  let {
    grades = [],
    projection,
    projectedTerm = "",
    uid,
    revision,
    instructors = [],
    instructorTrends = [],
    benchmarks,
    scope = "school",
    selectedTerm = $bindable(""),
    showTermSelect = true,
  }: {
    grades: any[];
    projection?: GradeProjection | null;
    projectedTerm?: string;
    uid: string;
    revision: string;
    instructors: any[];
    instructorTrends?: InstructorTrend[];
    benchmarks?: { all: Benchmarks; terms: Record<string, Benchmarks> };
    scope?: string;
    selectedTerm?: string;
    showTermSelect?: boolean;
  } = $props();
  let selectedInstructor = $state("");
  // Instructor subsets have different term/section coverage; do not compare them with whole courses.
  let filtered = $state<any[] | null>(null);
  let failure = $state("");
  let loading = $state(false);
  let controller: AbortController | undefined;
  onDestroy(() => controller?.abort());
  const keys = ["a", "ab", "b", "bc", "c", "d", "f"];
  const weights = [4, 3.5, 3, 2.5, 2, 1, 0];
  let source = $derived(filtered || grades);
  let display = $derived(gradeDisplay(source, selectedTerm, projectedTerm, !!projection?.interval && projection.target === selectedTerm));
  let isProjected = $derived(display.mode === "projected");
  let benchmark = $derived(selectedInstructor ? null : (display.term ? benchmarks?.terms[display.term]?.[scope] : benchmarks?.all[scope]));
  let selected = $derived(
    source.filter((r) => !display.term || r.term_id === display.term),
  );
  let bars = $derived(
    keys.map((k) => ({
      grade: k.toUpperCase(),
      count: selected.reduce((s, r) => s + (r[k] || 0), 0),
    })),
  );
  let trends = $derived.by(() => {
    const groups = new Map<string, any[]>();
    for (const r of grades.filter((row) => !display.term || row.term_id <= display.term))
      groups.set(r.term_id, [...(groups.get(r.term_id) || []), r]);
    return [...groups]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([term, rs]) => {
        const counts = keys.map((k) => rs.reduce((s, r) => s + (r[k] || 0), 0));
        const n = counts.reduce((a, b) => a + b, 0);
        return {
          term,
          gpa: n ? counts.reduce((s, n, i) => s + n * weights[i], 0) / n : null,
          n,
        };
      })
      .filter((r) => r.gpa != null);
  });
  const lineColors = ["var(--accent)", "var(--positive)", "#987746", "#866787"];
  let visibleInstructors = $derived(selectedInstructor ? instructorTrends.filter((instructor) => instructor.uid === selectedInstructor) : instructorTrends);
  let lineSeries = $derived([
    { key: "overall", label: "Course average", color: "var(--text)" },
    { key: "benchmark", label: scope === "school" ? "UW–Madison average" : `${scope} average`, color: "var(--muted)" },
    ...visibleInstructors.map((instructor) => ({ key: instructor.uid, label: courseTitle(instructor.name), color: lineColors[instructorTrends.findIndex((row) => row.uid === instructor.uid) % lineColors.length] })),
  ]);
  let trendRows = $derived(instructorChartRows(trends, visibleInstructors).filter((row) => !display.term || row.term <= display.term).map((row) => ({ ...row, label: termName(row.term), benchmark: benchmarks?.terms[row.term]?.[scope]?.gpa ?? null })));
  let trendDomain = $derived(gradeTrendDomain(trendRows, lineSeries.map((series) => series.key)));
  let total = $derived(bars.reduce((s, b) => s + b.count, 0));
  let gpa = $derived(
    total
      ? bars.reduce((s, b, i) => s + b.count * weights[i], 0) / total
      : null,
  );
  let topShare = $derived(
    total ? ((bars[0].count + bars[1].count) / total) * 100 : null,
  );
  async function change(instructor: string) {
    selectedInstructor = instructor;
    controller?.abort();
    const request = new AbortController();
    controller = request;
    filtered = null;
    failure = "";
    loading = false;
    if (!selectedInstructor) {
      return;
    }
    filtered = [];
    loading = true;
    try {
      const all: any[] = [];
      for (let page = 1; ; page++) {
        const q = new URLSearchParams({
          revision,
          instructor: selectedInstructor,
          page: String(page),
        });
        const r = await fetch(`/api/courses/${uid}/grades?${q}`, {
          signal: request.signal,
        });
        if (!r.ok)
          throw new Error(
            r.status === 409
              ? "Dataset updated. Reload this page."
              : "Unable to load grades.",
          );
        const body: any = await r.json();
        all.push(...body.items);
        if (all.length >= body.total) break;
      }
      if (request.signal.aborted) return;
      filtered = all;
      failure = "";
    } catch (e) {
      if ((e as Error).name !== "AbortError") failure = (e as Error).message;
    } finally {
      if (controller === request) loading = false;
    }
  }
  let percentageBars = $derived(
    bars.map((bar) => ({
      ...bar,
      percentage: total ? (bar.count / total) * 100 : 0,
    })),
  );
</script>

{#if display.mode === "fallback" && !loading && !failure}
  <p class="fallback-note">Latest available · {termName(display.term)}<span class="muted"> — not enough history to project {termName(selectedTerm)}.</span></p>
{/if}
<div class="grade-toolbar">
{#if !isProjected && display.mode !== "empty"}<div class="metric-strip">
  <div>
    <div class="metric-value" style:color={metricColor(gpa, benchmark?.gpa)}><MetricComparison value={gpa} reference={benchmark?.gpa} kind="gpa" label="Average GPA" group={scope === "school" ? "UW–Madison" : scope}><AnimatedNumber value={gpa} decimals={2} /></MetricComparison></div>
    <div class="metric-label">average GPA</div>
  </div>
  <div>
    <div class="metric-value" style:color={metricColor(topShare, benchmark?.topShare)}>
      <MetricComparison value={topShare} reference={benchmark?.topShare} kind="share" label="A / AB grades" group={scope === "school" ? "UW–Madison" : scope}><AnimatedNumber value={topShare} /><small>%</small></MetricComparison>
    </div>
    <div class="metric-label">A / AB grades</div>
  </div>
  <div>
    <div class="metric-value" style:color={metricColor(total, benchmark?.count)}><MetricComparison value={total} reference={benchmark?.count} label="Letter grades" group={scope === "school" ? "UW–Madison" : scope}><AnimatedNumber value={total} /></MetricComparison></div>
    <div class="metric-label">letter grades</div>
  </div>
</div>
{/if}
<div class="filters">
  {#if showTermSelect}<div class="filter-select"><span>Term</span><Select label="Term" bind:value={selectedTerm} options={[{ value: "", label: "All recorded terms" }, ...[...new Set<string>(grades.map((r) => r.term_id))].sort().reverse().map((term) => ({ value: term, label: termName(term) }))]} /></div>{/if}
  <div class="filter-select"><span>{isProjected ? "Historical instructor" : "Instructor"}</span><Select label="Instructor" bind:value={selectedInstructor} onChange={change} options={[{ value: "", label: "Course overall" }, ...instructors.map((i) => ({ value: i.instructor_uid, label: i.name }))]} /></div>
</div>
</div>
{#if failure}<p role="alert">{failure}</p>{/if}{#if loading}<p class="muted">
    Loading grades…
  </p>{/if}
  <div class="charts">
    <div>
      {#if isProjected}
        <GradeEstimate {projection} term={selectedTerm} />
      {:else}
      <h3>Grade distribution · % of letter grades</h3>
      {#if total}
      <div class="chart">
        <BarChart
          data={percentageBars}
          x="grade"
          y="percentage"
          c="grade"
          cDomain={keys.map((key) => key.toUpperCase())}
          cRange={[
            "var(--positive)",
            "var(--positive)",
            "var(--grade-mid)",
            "var(--grade-mid)",
            "var(--grade-mid)",
            "var(--negative)",
            "var(--negative)",
          ]}
          series={[
            {
              key: "percentage",
              label: "Percent of letter grades",
            },
          ]}
          height={220}
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
              ><AnimatedNumber value={total ? bar.count / total * 100 : 0} decimals={1} suffix="%" /></strong
            >
          </div>{/each}
      </div>
      {:else}<p class="empty">{display.mode === "empty" ? "No grades available yet." : "No recorded grades for this selection."}</p>{/if}
      {/if}
    </div>
    {#if trends.length > 1}<div>
        <h3>Grades over time{display.term ? ` · through ${termName(display.term)}` : ""}</h3>
        <div class="chart">
          <LineChart
            data={trendRows}
            x="label"
            series={lineSeries}
            xScale={scalePoint()}
            props={{ tooltip: { hideTotal: true, root: { pointerEvents: true }, list: { style: "max-height: 280px; overflow-y: auto" }, item: { format: (value: number) => value.toFixed(2) } }, xAxis: { tickOcclusion: true, tickSpacing: 90 }, spline: { curve: curveMonotoneX, strokeWidth: 1.8 } }}
            yDomain={trendDomain}
            yBaseline={undefined}
            yNice={false}
            legend={false}
            height={220}
          />
        </div>
      </div>{/if}
  </div>
  {#if selected.length}<details>
    <summary>Grade data</summary>
    <div class="table-scroll">
      <table>
        <thead
          ><tr
            ><th>Term</th>{#each keys as k}<th>{k.toUpperCase()}</th>{/each}<th
              >Total</th
            ></tr
          ></thead
        ><tbody
          >{#each selected as r}<tr
              ><td>{termName(r.term_id)}</td>{#each keys as k}<td
                  >{r[k] || 0}</td
                >{/each}<td>{r.total}</td></tr
            >{/each}</tbody
        >
      </table>
    </div>
  </details>{/if}
<details class="benchmark-note"><summary>About these comparisons</summary><p>{scope === "school" ? "UW–Madison" : scope} · matching recorded terms · all course levels.
  {#if selectedInstructor}Whole-course comparisons are unavailable for an instructor subset.
  {:else}Course averages for GPA and A/AB share; median course for grade count. Above/below does not imply teaching quality. Courses may have different historical coverage. Historical grades describe past outcomes; co-taught sections share one distribution. Instructor lines use grade-weighted section averages; all instructors are shown by default. Hover over a term to identify instructors, or select one above to isolate their history.{/if}
</p></details>

<style>

  .fallback-note { margin: 0 0 20px; font-size: 14px; }
  .grade-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
  .grade-toolbar .metric-strip { margin: 0; padding: 0; border: 0; gap: 32px; }
  .grade-toolbar .filters { margin: 0; gap: 12px; }
  .filter-select :global(.course-select-trigger) { max-width: 240px; }
  @media (max-width: 600px) {
    .grade-toolbar { gap: 16px; }
    .grade-toolbar .metric-strip { width: 100%; justify-content: space-between; gap: 16px; }
    .grade-toolbar .filters { width: 100%; }
    .filter-select { flex: 1; }
    .filter-select :global(.course-select-trigger) { max-width: 100%; }
  }

  .filter-select { display: grid; gap: 4px; min-width: 0; font-size: 13px; color: var(--muted); }
  .benchmark-note { font-size: 12px; line-height: 1.7; color: var(--muted); margin: 0; max-width: none; padding-bottom: 0; }

  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
    margin: 24px 0 16px;
  }
  h3 {
    font: 13px var(--font-sans);
    color: var(--muted);
    margin-bottom: 10px;
  }
  .chart {
    height: 230px;
    color: var(--text);
  }
  .chart :global(text) {
    font-size: 12px;
    fill: var(--muted);
    stroke: none;
  }
  .chart :global(.lc-bar) {
    stroke: none;
  }
  .grade-percentages {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 4px;
    margin: 12px 0;
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
