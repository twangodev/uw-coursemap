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
  import {
    instructorChartRows,
    gradeTrendDomain,
    type InstructorTrend,
  } from "$lib/instructor-trends";
  import { scalePoint } from "d3-scale";
  import { termName, courseTitle } from "$lib/format";
  let moreDetailsOpen = $state(false);
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
  let display = $derived(
    gradeDisplay(
      source,
      selectedTerm,
      projectedTerm,
      !!projection?.interval && projection.target === selectedTerm,
    ),
  );
  let isProjected = $derived(display.mode === "projected");
  let benchmark = $derived(
    selectedInstructor
      ? null
      : display.term
        ? benchmarks?.terms[display.term]?.[scope]
        : benchmarks?.all[scope],
  );
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
    for (const r of grades.filter(
      (row) => !display.term || row.term_id <= display.term,
    ))
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
  let visibleInstructors = $derived(
    selectedInstructor
      ? instructorTrends.filter(
          (instructor) => instructor.uid === selectedInstructor,
        )
      : instructorTrends,
  );
  let lineSeries = $derived([
    { key: "overall", label: "Course average", color: "var(--text)" },
    {
      key: "benchmark",
      label: scope === "school" ? "UW–Madison average" : `${scope} average`,
      color: "var(--muted)",
    },
    ...visibleInstructors.map((instructor) => ({
      key: instructor.uid,
      label: courseTitle(instructor.name),
      color:
        lineColors[
          instructorTrends.findIndex((row) => row.uid === instructor.uid) %
            lineColors.length
        ],
    })),
  ]);
  let trendRows = $derived(
    instructorChartRows(trends, visibleInstructors)
      .filter((row) => !display.term || row.term <= display.term)
      .map((row) => ({
        ...row,
        label: termName(row.term),
        benchmark: benchmarks?.terms[row.term]?.[scope]?.gpa ?? null,
      })),
  );
  let trendDomain = $derived(
    gradeTrendDomain(
      trendRows,
      lineSeries.map((series) => series.key),
    ),
  );
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
  <p class="mt-0 mb-5 text-[14px] fallback-note mx-0">
    Latest available · {termName(display.term)}<span class="muted">
      — not enough history to project {termName(selectedTerm)}.</span
    >
  </p>
{/if}
<div class="flex items-center justify-between gap-6 flex-wrap grade-toolbar">
  {#if !isProjected && display.mode !== "empty"}<div
      class="m-0 p-0 border-0 gap-8 metric-strip"
    >
      <div>
        <div
          class="metric-value"
          style:color={metricColor(gpa, benchmark?.gpa)}
        >
          <MetricComparison
            value={gpa}
            reference={benchmark?.gpa}
            kind="gpa"
            label="Average GPA"
            group={scope === "school" ? "UW–Madison" : scope}
            ><AnimatedNumber value={gpa} decimals={2} /></MetricComparison
          >
        </div>
        <div class="metric-label">average GPA</div>
      </div>
      <div>
        <div
          class="metric-value"
          style:color={metricColor(topShare, benchmark?.topShare)}
        >
          <MetricComparison
            value={topShare}
            reference={benchmark?.topShare}
            kind="share"
            label="A / AB grades"
            group={scope === "school" ? "UW–Madison" : scope}
            ><AnimatedNumber value={topShare} /><small>%</small
            ></MetricComparison
          >
        </div>
        <div class="metric-label">A / AB grades</div>
      </div>
      <div>
        <div
          class="metric-value"
          style:color={metricColor(total, benchmark?.count)}
        >
          <MetricComparison
            value={total}
            reference={benchmark?.count}
            label="Letter grades"
            group={scope === "school" ? "UW–Madison" : scope}
            ><AnimatedNumber value={total} /></MetricComparison
          >
        </div>
        <div class="metric-label">letter grades</div>
      </div>
    </div>
  {/if}
  <div class="m-0 gap-3 filters">
    {#if showTermSelect}<div
        class="grid gap-1 min-w-0 text-[13px] text-muted filter-select"
      >
        <span>Term</span><Select
          width="filter"
          label="Term"
          bind:value={selectedTerm}
          options={[
            { value: "", label: "All recorded terms" },
            ...[...new Set<string>(grades.map((r) => r.term_id))]
              .sort()
              .reverse()
              .map((term) => ({ value: term, label: termName(term) })),
          ]}
        />
      </div>{/if}
    <div class="grid gap-1 min-w-0 text-[13px] text-muted filter-select">
      <span>{isProjected ? "Historical instructor" : "Instructor"}</span><Select
        width="filter"
        label="Instructor"
        bind:value={selectedInstructor}
        onChange={change}
        options={[
          { value: "", label: "Course overall" },
          ...instructors.map((i) => ({
            value: i.instructor_uid,
            label: i.name,
          })),
        ]}
      />
    </div>
  </div>
</div>
{#if failure}<p role="alert">{failure}</p>{/if}{#if loading}<p class="muted">
    Loading grades…
  </p>{/if}
<div
  class="grid grid-cols-[minmax(0,_1fr)] gap-14 charts my-9 mx-0"
  class:projected-charts={isProjected && trends.length > 1}
>
  <div>
    {#if isProjected}
      <GradeEstimate {projection} term={selectedTerm} />
    {:else}
      <h3 class="text-[16px] font-medium text-foreground mt-0 mb-6 mx-0">
        Grade distribution · % of letter grades
      </h3>
      {#if total}
        <div class="h-67.5 text-foreground chart">
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
            height={260}
            props={{
              bars: {
                strokeWidth: 0,
                radius: 2,
              },
            }}
          />
        </div>
        <div class="grid grid-cols-7 gap-1 grade-percentages my-3 mx-0">
          {#each bars as bar}<div class="grid gap-1.5 text-center text-[12px]">
              <span class="text-muted">{bar.grade}</span><strong
                class="font-medium"
                ><AnimatedNumber
                  value={total ? (bar.count / total) * 100 : 0}
                  decimals={1}
                  suffix="%"
                /></strong
              >
            </div>{/each}
        </div>
      {:else}<p class="empty">
          {display.mode === "empty"
            ? "No grades available yet."
            : "No recorded grades for this selection."}
        </p>{/if}
    {/if}
  </div>
  {#if trends.length > 1}<div>
      <div class="grid gap-1.5 mb-5 trend-heading">
        <h3 class="text-[16px] font-medium text-foreground m-0">
          Grades over time
        </h3>
        {#if display.term}<p class="m-0 text-[12px] text-muted">
            Through {termName(display.term)}
          </p>{/if}
      </div>
      <div class="h-67.5 text-foreground chart">
        <LineChart
          data={trendRows}
          x="label"
          series={lineSeries}
          xScale={scalePoint()}
          props={{
            tooltip: {
              hideTotal: true,
              root: { pointerEvents: true },
              list: { style: "max-height: 280px; overflow-y: auto" },
              item: { format: (value: number) => value.toFixed(2) },
            },
            xAxis: { tickOcclusion: true, tickSpacing: 90 },
            spline: { curve: curveMonotoneX, strokeWidth: 1.8 },
          }}
          yDomain={trendDomain}
          yBaseline={undefined}
          yNice={false}
          legend={false}
          height={260}
        />
      </div>
    </div>{/if}
</div>
<details
  class="border-t border-t-border pt-5 pb-0 more-grade-details px-0"
  bind:open={moreDetailsOpen}
>
  <summary class="text-[15px] text-foreground cursor-pointer"
    >More grade details <span class="ml-3 text-muted text-[12px]"
      >Grade mix, volume & source data</span
    ></summary
  >
  {#if moreDetailsOpen}
    {#await import("./GradeHistory.svelte")}
      <p class="muted" role="status">Loading grade history…</p>
    {:then module}
      <module.default grades={source} through={selectedTerm} />
    {:catch}
      <p role="alert">
        Could not load the history charts. Close and reopen this section to
        retry.
      </p>
    {/await}
    {#if selected.length}<details>
        <summary>Grade data</summary>
        <div class="table-scroll">
          <table>
            <thead
              ><tr
                ><th>Term</th>{#each keys as k}<th>{k.toUpperCase()}</th
                  >{/each}<th>Total</th></tr
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
    <details
      class="text-[12px] leading-[1.7] text-muted m-0 max-w-none pb-0 benchmark-note"
    >
      <summary>About these comparisons</summary>
      <p>
        {scope === "school" ? "UW–Madison" : scope} · matching recorded terms · all
        course levels.
        {#if selectedInstructor}Whole-course comparisons are unavailable for an
          instructor subset.
        {:else}Course averages for GPA and A/AB share; median course for grade
          count. Above/below does not imply teaching quality. Courses may have
          different historical coverage. Historical grades describe past
          outcomes; co-taught sections share one distribution. Instructor lines
          use grade-weighted section averages; all instructors are shown by
          default. Hover over a term to identify instructors, or select one
          above to isolate their history.{/if}
      </p>
    </details>
  {/if}
</details>

<style>
  .more-grade-details[open] > summary {
    margin-bottom: 28px;
  }
  @media (min-width: 960px) {
    .charts.projected-charts {
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.4fr);
      gap: 48px;
      align-items: start;
    }
  }
  @media (max-width: 600px) {
    .more-grade-details > summary span {
      display: block;
      margin: 4px 0 0 18px;
    }
  }
  @media (max-width: 600px) {
    .grade-toolbar {
      gap: 16px;
    }
    .grade-toolbar .metric-strip {
      width: 100%;
      justify-content: space-between;
      gap: 16px;
    }
    .grade-toolbar .filters {
      width: 100%;
    }
    .filter-select {
      flex: 1;
    }
  }
  h3 {
    font-family: inherit;
  }
  .chart :global(text) {
    font-size: 12px;
    fill: var(--muted);
    stroke: none;
  }
  .chart :global(.lc-bar) {
    stroke: none;
  }
</style>
