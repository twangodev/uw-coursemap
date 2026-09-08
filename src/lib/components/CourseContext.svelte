<script lang="ts">
  import { courseFit } from "$lib/course-fit";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { metricColor } from "$lib/grade-benchmarks";
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  let { context: catalog, scope = "school", term = "", sections = [] }: { context: any; scope?: string; term?: string; sections?: any[] } = $props();
  let context = $derived(term ? catalog.terms[term] : catalog.all);
  let benchmark = $derived(term ? catalog.benchmarks.terms[term]?.[scope] : catalog.benchmarks.all[scope]);
  let comparison = $derived(
    scope !== "school"
      ? context?.departments.find((row: any) => row.subject === scope)
          ?.comparison
      : context?.university,
  );
  let fitTerm = $derived(term && !context ? Object.keys(catalog.terms).filter(t => t < term && catalog.terms[t]).sort().at(-1) : term);
  let fitContext = $derived(fitTerm ? catalog.terms[fitTerm] : context);
  let fitBenchmark = $derived(fitTerm ? catalog.benchmarks.terms[fitTerm]?.[scope] : benchmark);
  let sectionTerm = $derived(term || sections.map(section => section.term_id).sort().at(-1));
  let fit = $derived(courseFit({ gpa: fitContext?.count >= 30 ? fitContext.gpa : null, reference: fitBenchmark?.gpa, group: scope === "school" ? "UW–Madison" : scope, sections: sections.filter(section => section.term_id === sectionTerm) }));
</script>

{#if (comparison && context) || fit}
  <section class="course-context" aria-labelledby="context-title">
    <div class="context-heading">
      <div>
        <h2 id="context-title">Where this course fits</h2>
        <p class="muted">
          {term ? termName(term) : "All recorded terms"} · all course levels
        </p>
      </div>
      <span class="muted">{scope === "school" ? "UW–Madison" : scope}</span>
    </div>
    {#if fit}<p class="fit-summary">{fit}</p>
      <p class="fit-source muted">{fitContext && fitBenchmark ? `Grades: ${fitTerm ? termName(fitTerm) : "all recorded terms"}. ` : ""}{sections.some(section => section.term_id === sectionTerm && section.enrolled > 0) ? `Section enrollment: ${termName(sectionTerm)} snapshot.` : ""}</p>
    {/if}
    {#if comparison && context}<div class="context-grid">
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
        {comparison.size} courses over {term ? "the same term" : "the course’s recorded terms"}, each with at least 30
        recorded letter grades. Cross-listed courses count once. GPA is not a measure
        of difficulty or teaching quality. The typical course is the median by recorded
        grade count; tied values are not counted as lower.
      </p>
      <p>Descriptions compare GPA with this group’s average: at least 0.20 higher or lower; otherwise close to average. Section size uses median recorded enrollment: small up to 30, mid-sized 31–99, large 100+. Lectures and discussion/lab sections are described separately.</p>
    </details>{/if}
  </section>
{:else}<p class="muted">Not enough comparable courses for {term ? termName(term) : "these recorded terms"} in {scope === "school" ? "UW–Madison" : scope}.</p>{/if}

<style>
  .fit-summary { max-width: 68ch; font-size: 18px; line-height: 1.65; margin-bottom: 10px; }
  .fit-source { font-size: 12px; margin-bottom: 28px; }
  .course-context {
    padding: 24px 0 0;
    border-top: 1px solid var(--border);
  }
  .context-heading {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 24px;
    margin-bottom: 24px;
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
    gap: 32px;
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
    padding-bottom: 0;
    font-size: 13px;
    margin-top: 20px;
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
      gap: 28px;
    }
    .course-context {
      padding: 24px 0 0;
    }
  }
</style>
