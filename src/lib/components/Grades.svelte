<script lang="ts">
  import { onDestroy } from "svelte";
  import { BarChart, LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { termName } from "$lib/format";
  let {
    grades = [],
    uid,
    revision,
    instructors = [],
  }: {
    grades: any[];
    uid: string;
    revision: string;
    instructors: any[];
  } = $props();
  let selectedTerm = $state("");
  let selectedInstructor = $state("");
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
  async function change() {
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
</script>

<div class="metric-strip">
  <div>
    <div class="metric-value">{gpa?.toFixed(2) ?? "—"}</div>
    <div class="metric-label">average GPA</div>
  </div>
  <div>
    <div class="metric-value">
      {topShare?.toFixed(0) ?? "—"}<small>%</small>
    </div>
    <div class="metric-label">A / AB grades</div>
  </div>
  <div>
    <div class="metric-value">{total.toLocaleString()}</div>
    <div class="metric-label">letter grades</div>
  </div>
</div>
<div class="filters">
  <label
    >Term<select bind:value={selectedTerm}
      ><option value="">All recorded terms</option
      >{#each [...new Set(grades.map((r) => r.term_id))]
        .sort()
        .reverse() as t}<option value={t}>{termName(t)}</option>{/each}</select
    ></label
  ><label
    >Instructor<select bind:value={selectedInstructor} onchange={change}
      ><option value="">Course overall</option>{#each instructors as i}<option
          value={i.instructor_uid}>{i.name}</option
        >{/each}</select
    ></label
  >
</div>
{#if failure}<p role="alert">{failure}</p>{/if}{#if loading}<p class="muted">
    Loading grades…
  </p>{/if}
{#if selected.length}<p class="mono muted">
    {bars.reduce((s, b) => s + b.count, 0).toLocaleString()} letter grades · other
    outcomes excluded from GPA
  </p>
  <div class="charts">
    <div>
      <h3>Grade distribution</h3>
      <div class="chart">
        <BarChart
          data={bars}
          x="grade"
          y="count"
          series={[{ key: "count", label: "Students", color: "var(--accent)" }]}
          height={250}
        />
      </div>
    </div>
    {#if trends.length > 1}<div>
        <h3>Grades over time</h3>
        <div class="chart">
          <LineChart
            data={trends}
            x="term"
            y="gpa"
            series={[{ key: "gpa", label: "GPA", color: "var(--accent)" }]}
            xScale={scalePoint()}
            props={{ xAxis: { tickOcclusion: true, tickSpacing: 90 } }}
            yDomain={[0, 4]}
            height={250}
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
  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
    margin: 1.5rem 0;
  }
  h3 {
    font: 11px var(--font-mono);
    color: var(--muted);
    margin-bottom: 10px;
  }
  .chart {
    height: 260px;
    color: var(--text);
  }
</style>
