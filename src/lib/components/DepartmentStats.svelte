<script lang="ts">
  import type { DepartmentStatistics } from "$lib/view-models";
  import { BarChart, LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX } from "d3-shape";
  import { gradeTrendDomain } from "$lib/instructor-trends";
  import { termName } from "$lib/format";
  import { metricColor } from "$lib/grade-benchmarks";
  import Disclosure from "./Disclosure.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import MetricComparison from "./MetricComparison.svelte";
  let {
    stats,
    term = "",
    detail = false,
  }: {
    stats: DepartmentStatistics;
    term?: string;
    detail?: boolean;
  } = $props();
  let current = $derived(term ? stats.terms[term] : stats.all);
  let bars = $derived(
    ["A", "AB", "B", "BC", "C", "D", "F"].map((grade, i) => ({
      grade,
      department: current?.count
        ? (current.counts[i] / current.count) * 100
        : null,
      university: current?.university.count
        ? (current.university.counts[i] / current.university.count) * 100
        : null,
    })),
  );
  let offerings = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => (!term || t <= term) && r.courses != null)
      .map(([t, r]) => ({ term: termName(t), courses: r.courses })),
  );
  let lastGraded = $derived(
    Object.keys(stats.terms)
      .filter((t) => stats.terms[t].count && (!term || t < term))
      .sort()
      .at(-1),
  );
  let trends = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => (!term || t <= term) && r.count)
      .map(([t, r]) => ({
        term: termName(t),
        department: r.gpa,
        university: r.university.gpa,
      })),
  );
</script>

<section
  class="border-t border-t-border department-stats py-7 px-0"
  aria-label={term
    ? "Selected-term department statistics"
    : "Department overview"}
>
  <div class="flex justify-between items-baseline gap-5 mb-7 heading">
    <h2 class="text-[26px] font-medium m-0">
      {detail
        ? "Across course levels"
        : term
          ? termName(term)
          : "The department at a glance"}
    </h2>
    <span class="text-[12px] muted"
      >{term ? "Recorded this term" : "All recorded grades"}</span
    >
  </div>
  {#if detail}
    {#if current?.levels?.length}<div class="level-chart">
        <BarChart
          data={current.levels
            .filter((row) => row.count >= 30)
            .map((row) => ({
              ...row,
              universityGpa:
                row.university.count >= 30 ? row.university.gpa : null,
            }))}
          seriesLayout="group"
          y="level"
          orientation="horizontal"
          xDomain={[0, 4]}
          series={[
            { key: "gpa", label: "Department GPA", color: "var(--accent)" },
            {
              key: "universityGpa",
              label: "UW–Madison GPA",
              color: "var(--border)",
            },
          ]}
          props={{ bars: { strokeWidth: 0 }, tooltip: { hideTotal: true } }}
          height={260}
        />
      </div>
      <p class="text-[12px] text-muted leading-[1.7] max-w-[85ch] note">
        Course-number ranges · at least 30 letter grades per range. Levels
        describe course numbers, not how difficult a class is.
      </p>{:else}<p class="muted">No released grades for this term.</p>{/if}
  {:else}
    <div class="flex flex-wrap gap-y-7 gap-x-12 mb-7 numbers">
      {#if !term || current?.count}
        {#each [{ label: "average GPA", value: current?.gpa, reference: current?.university.gpa, kind: "gpa", decimals: 2 }, { label: "A / AB grades", value: current?.topShare, reference: current?.university.topShare, kind: "share", decimals: 0 }, { label: "letter grades", value: current?.count || null, reference: null, kind: "count", decimals: 0 }] as m}<div
            class="grid gap-[9px]"
          >
            <strong
              class="text-[38px] font-medium tracking-[-0.04em]"
              style:color={metricColor(m.value ?? null, m.reference)}
              ><MetricComparison
                value={m.value ?? null}
                reference={m.reference}
                kind={m.kind === "count"
                  ? undefined
                  : (m.kind as "gpa" | "share")}
                label={m.label}
                group="UW–Madison"
                ><AnimatedNumber
                  value={m.value ?? null}
                  decimals={m.decimals}
                  suffix={m.kind === "share" ? "%" : ""}
                /></MetricComparison
              ></strong
            ><span class="text-[12px] text-muted">{m.label}</span>
          </div>{/each}
      {/if}
      {#if term}<div class="grid gap-[9px]">
          <strong class="text-[38px] font-medium tracking-[-0.04em]"
            ><AnimatedNumber value={current?.courses ?? null} /></strong
          ><span class="text-[12px] text-muted">courses with offerings</span>
        </div>
        <div class="grid gap-[9px]">
          <strong class="text-[38px] font-medium tracking-[-0.04em]"
            ><AnimatedNumber value={current?.instructors ?? null} /></strong
          ><span class="text-[12px] text-muted">instructors recorded</span>
        </div>{/if}
    </div>
    {#if !term}<div class="grid grid-cols-[1fr_1fr] gap-10 charts">
        <div class="min-w-0">
          <h3 class="text-[13px] font-normal text-muted mb-5">
            How grades break down
          </h3>
          <BarChart
            data={bars}
            seriesLayout="group"
            x="grade"
            series={[
              {
                key: "department",
                label: "Department · %",
                color: "var(--accent)",
              },
              {
                key: "university",
                label: "UW–Madison · %",
                color: "var(--border)",
              },
            ]}
            height={205}
            props={{
              bars: { strokeWidth: 0, radius: 2 },
              tooltip: { hideTotal: true },
            }}
          />
        </div>
        <div class="min-w-0">
          <h3 class="text-[13px] font-normal text-muted mb-5">
            Grades over time
          </h3>
          <LineChart
            data={trends}
            x="term"
            xScale={scalePoint()}
            yDomain={gradeTrendDomain(trends, ["department", "university"])}
            yBaseline={undefined}
            yNice={false}
            series={[
              {
                key: "department",
                label: "Department",
                color: "var(--accent)",
              },
              { key: "university", label: "UW–Madison", color: "var(--muted)" },
            ]}
            height={205}
            props={{
              spline: { curve: curveMonotoneX },
              xAxis: { tickOcclusion: true },
              tooltip: { hideTotal: true },
            }}
          />
        </div>
      </div>
    {:else if !current?.count}<p
        class="text-[12px] text-muted leading-[1.7] max-w-[85ch] note"
      >
        Grades have not been recorded for this term. Historical results remain
        in the overview above.
      </p>{/if}
  {/if}
  {#if detail && offerings.length}<div class="offering-history">
      <h3>Recorded offerings over time</h3>
      {#if offerings.length > 1}<BarChart
          data={offerings}
          x="term"
          series={[
            {
              key: "courses",
              label: "Courses with offering records",
              color: "var(--accent)",
            },
          ]}
          height={180}
        />{:else}<p
          class="text-[12px] text-muted leading-[1.7] max-w-[85ch] note"
        >
          Offering snapshots currently cover {offerings[0].term}. Earlier grade
          records do not provide a complete offering history.
        </p>{/if}
    </div>{/if}
  {#if !term}<p class="text-[12px] text-muted leading-[1.7] max-w-[85ch] note">
      Red: department · Gray: UW–Madison
    </p>
    <Disclosure title="About these statistics" variant="compact" lazy={false}>
      <p class="text-[12px] text-muted leading-[1.7] max-w-[85ch] note">
        GPA and percentages are weighted by recorded letter grades. UW
        comparisons use the same terms. Cross-listed courses count once within
        this department and once across UW; department totals should not be
        added together. Grade counts are not unique students. Offering counts
        reflect captured records, not a complete historical schedule.
      </p>
    </Disclosure>{/if}
</section>

<style>
  @media (max-width: 760px) {
    .charts {
      grid-template-columns: 1fr;
    }
    .heading {
      align-items: start;
      flex-direction: column;
      gap: 10px;
    }
    .numbers {
      gap: 24px 32px;
    }
    .numbers strong {
      font-size: 32px;
    }
  }
</style>
