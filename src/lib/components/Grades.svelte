<script lang="ts">
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import Select from "./Select.svelte";
  import MetricComparison from "./MetricComparison.svelte";
  import { metricColor, type Benchmarks } from "$lib/grade-benchmarks";
  import { onDestroy } from "svelte";
  import { BarChart, LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { termName } from "$lib/format";
  let {
    grades = [],
    uid,
    revision,
    instructors = [],
    benchmarks,
    scope = "school",
    selectedTerm = $bindable(""),
    showTermSelect = true,
  }: {
    grades: any[];
    uid: string;
    revision: string;
    instructors: any[];
    benchmarks?: { all: Benchmarks; terms: Record<string, Benchmarks> };
    scope?: string;
    selectedTerm?: string;
    showTermSelect?: boolean;
  } = $props();
  let selectedInstructor = $state("");
  // Instructor subsets have different term/section coverage; do not compare them with whole courses.
  let benchmark = $derived(selectedInstructor ? null : (selectedTerm ? benchmarks?.terms[selectedTerm]?.[scope] : benchmarks?.all[scope]));
  let filtered = $state<any[] | null>(null);
  let failure = $state("");
  let loading = $state(false);
  let controller: AbortController | undefined;
  onDestroy(() => controller?.abort());
  const keys = ["a", "ab", "b", "bc", "c", "d", "f"];
  const weights = [4, 3.5, 3, 2.5, 2, 1, 0];
  let source = $derived(filtered || grades);
  let selected = $derived(
    source.filter((r) => !selectedTerm || r.term_id === selectedTerm),
  );
  let bars = $derived(
    keys.map((k) => ({
      grade: k.toUpperCase(),
      count: selected.reduce((s, r) => s + (r[k] || 0), 0),
    })),
  );
  let trends = $derived.by(() => {
    const groups = new Map<string, any[]>();
    for (const r of source)
      groups.set(r.term_id, [...(groups.get(r.term_id) || []), r]);
    return [...groups]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([term, rs]) => {
        const counts = keys.map((k) => rs.reduce((s, r) => s + (r[k] || 0), 0));
        const n = counts.reduce((a, b) => a + b, 0);
        return {
          term: termName(term),
          gpa: n ? counts.reduce((s, n, i) => s + n * weights[i], 0) / n : null,
          n,
        };
      })
      .filter((r) => r.gpa != null);
  });
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

<div class="metric-strip">
  <div>
    <div class="metric-value" style:color={metricColor(gpa, benchmark?.gpa)}><AnimatedNumber value={gpa} decimals={2} /></div>
    <div class="metric-label">average GPA</div>
    <MetricComparison value={gpa} reference={benchmark?.gpa} kind="gpa" />
  </div>
  <div>
    <div class="metric-value" style:color={metricColor(topShare, benchmark?.topShare)}>
      <AnimatedNumber value={topShare} /><small>%</small>
    </div>
    <div class="metric-label">A / AB grades</div>
    <MetricComparison value={topShare} reference={benchmark?.topShare} kind="share" />
  </div>
  <div>
    <div class="metric-value" style:color={metricColor(total, benchmark?.count)}><AnimatedNumber value={total} /></div>
    <div class="metric-label">letter grades</div>
    <MetricComparison value={total} reference={benchmark?.count} />
  </div>
</div>
<div class="filters">
  {#if showTermSelect}<div class="filter-select"><span>Term</span><Select label="Term" bind:value={selectedTerm} options={[{ value: "", label: "All recorded terms" }, ...[...new Set<string>(grades.map((r) => r.term_id))].sort().reverse().map((term) => ({ value: term, label: termName(term) }))]} /></div>{/if}
  <div class="filter-select"><span>Instructor</span><Select label="Instructor" bind:value={selectedInstructor} onChange={change} options={[{ value: "", label: "Course overall" }, ...instructors.map((i) => ({ value: i.instructor_uid, label: i.name }))]} /></div>
</div>
<p class="benchmark-note">{scope === "school" ? "UW–Madison" : scope} · matching recorded terms · all course levels.
  {#if selectedInstructor}Whole-course comparisons are unavailable for an instructor subset.
  {:else}Course averages for GPA and A/AB share; median course for grade count. Above/below does not imply teaching quality. Courses may have different historical coverage.{/if}
</p>
{#if failure}<p role="alert">{failure}</p>{/if}{#if loading}<p class="muted">
    Loading grades…
  </p>{/if}
{#if selected.length}
  <div class="charts">
    <div>
      <h3>Grade distribution · % of letter grades</h3>
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
    </div>
    {#if trends.length > 1}<div>
        <h3>Grades over time</h3>
        <div class="chart">
          <LineChart
            data={trends}
            x="term"
            y="gpa"
            series={[{ key: "gpa", label: "GPA", color: "var(--text)" }]}
            xScale={scalePoint()}
            props={{ xAxis: { tickOcclusion: true, tickSpacing: 90 } }}
            yDomain={[0, 4]}
            height={220}
          />
        </div>
      </div>{/if}
  </div>
  <details>
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
  </details>{:else}<p class="empty">
    No recorded grades for this selection.
  </p>{/if}
<p class="muted">
  Historical grades describe past outcomes. Co-taught sections share one
  distribution.
</p>

<style>
  .filter-select { display: grid; gap: 8px; min-width: 0; font-size: 13px; color: var(--muted); }
  .benchmark-note { font-size: 12px; line-height: 1.7; color: var(--muted); margin: 12px 0 24px; max-width: 85ch; }

  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
    margin: 1.5rem 0;
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
