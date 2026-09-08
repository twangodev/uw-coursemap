<script lang="ts">
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { metricColor } from "$lib/grade-benchmarks";
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  let { context, scope = "school" }: { context: any; scope?: string } = $props();
  let benchmark = $derived(context.benchmarks.terms[context.term]?.[scope]);
  let comparison = $derived(
    scope !== "school"
      ? context.departments.find((row: any) => row.subject === scope)
          ?.comparison
      : context.university,
  );
</script>

{#if comparison}
  <section class="course-context" aria-labelledby="context-title">
    <div class="context-heading">
      <div>
        <h2 id="context-title">Where this course fits</h2>
        <p class="muted">
          {termName(context.term)} · all course levels
        </p>
      </div>
      <span class="muted">{scope === "school" ? "UW–Madison" : scope}</span>
    </div>
    <div class="context-grid">
      <div>
        <p class="context-number" style:color={metricColor(context.gpa, benchmark?.gpa)}><AnimatedNumber value={context.gpa} decimals={2} /> <span>GPA</span></p>
        <p>
          Higher than <strong><AnimatedNumber value={comparison.gpaPercentile} decimals={0} />%</strong> of other courses
          in this group.
        </p>
        <div class="context-chart">
          <BarChart
            data={comparison.histogram}
            x="range"
            y="count"
            c={(row: any) => (row.current ? "current" : "other")}
            cDomain={["other", "current"]}
            cRange={["var(--border)", "var(--accent)"]}
            series={[{ key: "count", label: "Courses" }]}
            height={185}
            props={{
              bars: {
                strokeWidth: 0,
                radius: 2,
              },
              xAxis: { tickOcclusion: true, tickSpacing: 65 },
            }}
          />
        </div>
        <p class="chart-caption">Course GPAs · red marks this course’s range</p>
      </div>
      <div class="course-scale">
        <p class="context-number" style:color={metricColor(context.count, benchmark?.count)}>
          <AnimatedNumber value={context.count} decimals={0} /> <span>letter grades</span>
        </p>
        <p>
          More recorded grades than <strong
            ><AnimatedNumber value={comparison.countPercentile} decimals={0} />%</strong
          > of other courses in this group.
        </p>
        <div class="scale-comparison">
          <BarChart
            data={[
              { label: "This course", count: context.count },
              { label: "Median course", count: comparison.medianCount },
            ]}
            x="count"
            y="label"
            orientation="horizontal"
            c="label"
            cDomain={["This course", "Median course"]}
            cRange={["var(--accent)", "var(--border)"]}
            series={[{ key: "count", label: "Letter grades" }]}
            height={155}
            props={{ bars: { strokeWidth: 0, radius: 2 } }}
          />
        </div>
        <p class="scale-caption">
          Typical course in this group: <strong
            ><AnimatedNumber value={comparison.medianCount} decimals={1} /></strong
          > letter grades.
        </p>
        <p class="chart-caption">
          A sense of course scale, not unique students or typical section size.
        </p>
      </div>
    </div>
    <details class="comparison-method">
      <summary>About this comparison</summary>
      <p>
        {comparison.size} courses in the same term, each with at least 30
        recorded letter grades. Cross-listed courses count once. GPA is not a measure
        of difficulty or teaching quality. The typical course is the median by recorded
        grade count; tied values are not counted as lower.
      </p>
    </details>
  </section>
{/if}

<style>
  .course-context {
    padding: 40px 0;
    border-top: 1px solid var(--border);
  }
  .context-heading {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 24px;
    margin-bottom: 36px;
  }
  h2 {
    font-size: 25px;
    margin-bottom: 8px;
  }
  .context-heading p {
    font-size: 14px;
  }
  .context-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 56px;
  }
  .context-number {
    font-size: 40px;
    letter-spacing: -0.04em;
    line-height: 1.2;
    margin-bottom: 18px;
  }
  .context-number span {
    font-size: 15px;
    letter-spacing: 0;
    color: var(--muted);
  }
  .context-grid p:not(.context-number) {
    max-width: 42ch;
    line-height: 1.65;
  }
  .context-chart {
    height: 195px;
    margin-top: 26px;
  }
  .chart-caption {
    font-size: 12px;
    color: var(--muted);
    margin-top: 14px;
  }
  .scale-comparison {
    height: 165px;
    margin: 26px 0 14px;
  }
  .scale-caption {
    font-size: 13px;
  }

  .comparison-method {
    font-size: 13px;
    margin-top: 36px;
  }
  .comparison-method p {
    max-width: 80ch;
    margin-top: 16px;
    line-height: 1.7;
  }
  @media (max-width: 760px) {
    .context-heading {
      flex-direction: column;
    }
    .context-grid {
      grid-template-columns: 1fr;
      gap: 40px;
    }
    .course-context {
      padding: 32px 0;
    }
  }
</style>
