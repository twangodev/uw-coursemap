<script lang="ts">
  import { ArrowLeftRight } from "@lucide/svelte";
  import { courseFit } from "$lib/course-fit";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { metricColor } from "$lib/grade-benchmarks";
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  let { context: catalog, scope = "school", term = "", sections = [], subjects = [], onScopeChange }: { context: any; scope?: string; term?: string; sections?: any[]; subjects?: string[]; onScopeChange?: (scope: string) => void } = $props();
  let comparisonScopes = $derived(["school", ...new Set(subjects.filter(subject => subject !== "school"))]);
  let nextScope = $derived(comparisonScopes[(comparisonScopes.indexOf(scope) + 1) % comparisonScopes.length]);
  let contextTerm = $derived(term && !catalog.terms[term] ? Object.keys(catalog.terms).filter(t => t < term && catalog.terms[t]).sort().at(-1) : term);
  let context = $derived(contextTerm ? catalog.terms[contextTerm] : term ? null : catalog.all);
  let benchmark = $derived(contextTerm ? catalog.benchmarks.terms[contextTerm]?.[scope] : term ? null : catalog.benchmarks.all[scope]);
  let comparison = $derived(
    scope !== "school"
      ? context?.departments.find((row: any) => row.subject === scope)
          ?.comparison
      : context?.university,
  );
  let sectionTerm = $derived(term || sections.map(section => section.term_id).sort().at(-1));
  let fit = $derived(courseFit({ gpa: context?.count >= 30 ? context.gpa : null, reference: benchmark?.gpa, group: scope === "school" ? "UW–Madison" : scope, sections: sections.filter(section => section.term_id === sectionTerm) }));
</script>

{#if (comparison && context) || fit}
  <section class="course-context" aria-labelledby="context-title">
    <div class="context-heading">
      <div>
        <h2 id="context-title">Where this course fits relative to <button type="button" class="inline-comparison" aria-label="Course fit comparison" title={`Compare with ${nextScope === "school" ? "UW–Madison" : nextScope}`} onclick={() => onScopeChange?.(nextScope)}>{scope === "school" ? "UW–Madison" : scope}<span class="swap-icon" aria-hidden="true"><ArrowLeftRight size={17} strokeWidth={1.5} /></span></button></h2>
        <p class="muted">
          {contextTerm && contextTerm !== term ? `Latest available grades · ${termName(contextTerm)}` : contextTerm ? termName(contextTerm) : term ? termName(term) : "All recorded terms"} · all course levels
        </p>
      </div>
    </div>
    {#if fit}<p class="fit-summary">{fit}</p>
      <p class="fit-source muted">{context && benchmark ? `Grades: ${contextTerm ? termName(contextTerm) : "all recorded terms"}. ` : ""}{sections.some(section => section.term_id === sectionTerm && section.enrolled > 0) ? `Section enrollment: ${termName(sectionTerm)} snapshot.` : ""}</p>
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
  .inline-comparison { display: inline-flex; align-items: baseline; gap: 8px; max-width: 100%; padding: 0 0 2px; border: 0; border-bottom: 1px dashed var(--muted); border-radius: 0; background: transparent; color: inherit; font: inherit; line-height: inherit; cursor: pointer; }
  .swap-icon { display: inline-flex; align-self: center; opacity: 0; transition: opacity 140ms ease; }
  .inline-comparison:hover .swap-icon, .inline-comparison:focus-visible .swap-icon { opacity: 1; }
  @media (prefers-reduced-motion: reduce) { .swap-icon { transition: none; } }
  .inline-comparison:hover { color: var(--accent); border-color: var(--accent); }
  .inline-comparison:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
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
