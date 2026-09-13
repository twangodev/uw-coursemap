<script lang="ts">
  import { ArrowLeftRight } from "@lucide/svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { metricColor } from "$lib/grade-benchmarks";
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  let {
    context: catalog,
    scope = "school",
    term = "",
    subjects = [],
    onScopeChange,
  }: {
    context: any;
    scope?: string;
    term?: string;
    subjects?: string[];
    onScopeChange?: (scope: string) => void;
  } = $props();
  let comparisonScopes = $derived([
    "school",
    ...new Set(subjects.filter((subject) => subject !== "school")),
  ]);
  let nextScope = $derived(
    comparisonScopes[
      (comparisonScopes.indexOf(scope) + 1) % comparisonScopes.length
    ],
  );
  let contextTerm = $derived(
    term && !catalog.terms[term]
      ? Object.keys(catalog.terms)
          .filter((t) => t < term && catalog.terms[t])
          .sort()
          .at(-1)
      : term,
  );
  let context = $derived(
    contextTerm ? catalog.terms[contextTerm] : term ? null : catalog.all,
  );
  let benchmark = $derived(
    contextTerm
      ? catalog.benchmarks.terms[contextTerm]?.[scope]
      : term
        ? null
        : catalog.benchmarks.all[scope],
  );
  let comparison = $derived(
    scope !== "school"
      ? context?.departments.find((row: any) => row.subject === scope)
          ?.comparison
      : context?.university,
  );
</script>

{#if comparison && context}
  <section
    class="pt-6 pb-0 border-t border-t-border course-context px-0"
    aria-labelledby="context-title"
  >
    <div class="flex justify-between items-start gap-6 mb-6 context-heading">
      <div>
        <h2 class="text-[25px] mb-2" id="context-title">
          Where this course fits relative to <button
            type="button"
            class="inline-flex items-baseline gap-2 max-w-full pt-0 pb-0.5 border-0 rounded-none bg-transparent text-inherit leading-[inherit] cursor-pointer inline-comparison px-0"
            aria-label="Course fit comparison"
            title={`Compare with ${nextScope === "school" ? "UW–Madison" : nextScope}`}
            onclick={() => onScopeChange?.(nextScope)}
            >{scope === "school" ? "UW–Madison" : scope}<span
              class="inline-flex self-center opacity-0 swap-icon"
              aria-hidden="true"
              ><ArrowLeftRight size={17} strokeWidth={1.5} /></span
            ></button
          >
        </h2>
        <p class="text-[14px] muted">
          {contextTerm && contextTerm !== term
            ? `Latest available grades · ${termName(contextTerm)}`
            : contextTerm
              ? termName(contextTerm)
              : term
                ? termName(term)
                : "All recorded terms"} · all course levels
        </p>
      </div>
    </div>
    {#if comparison && context}<div
        class="grid grid-cols-[1fr_1fr] gap-8 context-grid"
      >
        <div>
          <p
            class="text-[40px] tracking-[-0.04em] leading-[1.2] mb-4.5 context-number"
            style:color={metricColor(context.gpa, benchmark?.gpa)}
          >
            <AnimatedNumber value={context.gpa} decimals={2} />
            <span class="text-[15px] tracking-[0] text-muted">GPA</span>
          </p>
          <p>
            Higher than <strong
              ><AnimatedNumber
                value={comparison.gpaPercentile}
                decimals={0}
              />%</strong
            > of other courses in this group.
          </p>
          <div class="h-[195px] mt-6.5 context-chart">
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
          <p class="text-[12px] text-muted mt-3.5 chart-caption">
            Course GPAs · red marks this course’s range
          </p>
        </div>
        <div class="course-scale">
          <p
            class="text-[40px] tracking-[-0.04em] leading-[1.2] mb-4.5 context-number"
            style:color={metricColor(context.count, benchmark?.count)}
          >
            <AnimatedNumber value={context.count} decimals={0} />
            <span class="text-[15px] tracking-[0] text-muted"
              >letter grades</span
            >
          </p>
          <p>
            More recorded grades than <strong
              ><AnimatedNumber
                value={comparison.countPercentile}
                decimals={0}
              />%</strong
            > of other courses in this group.
          </p>
          <div class="h-[165px] mt-6.5 mb-3.5 scale-comparison mx-0">
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
          <p class="text-[13px] scale-caption">
            Typical course in this group: <strong
              ><AnimatedNumber
                value={comparison.medianCount}
                decimals={1}
              /></strong
            > letter grades.
          </p>
        </div>
      </div>
      <details class="pb-0 text-[13px] mt-5 comparison-method">
        <summary>About this comparison</summary>
        <p class="mt-4 leading-[1.7]">
          {comparison.size} courses over {term
            ? "the same term"
            : "the course’s recorded terms"}, each with at least 30 recorded
          letter grades. Cross-listed courses count once. GPA is not a measure
          of difficulty or teaching quality. The typical course is the median by
          recorded grade count; tied values are not counted as lower. Grade
          counts describe course scale, not unique students or typical section
          size.
        </p>
        <p class="mt-4 leading-[1.7]">
          Descriptions compare GPA with this group’s average: at least 0.20
          higher or lower; otherwise close to average. Section size uses median
          recorded enrollment: small up to 30, mid-sized 31–99, large 100+.
          Lectures and discussion/lab sections are described separately.
        </p>
      </details>{/if}
  </section>
{:else}<p class="muted">
    Not enough comparable courses for {term
      ? termName(term)
      : "these recorded terms"} in {scope === "school" ? "UW–Madison" : scope}.
  </p>{/if}

<style>
  .inline-comparison {
    border-bottom: 1px dashed var(--muted);
    font: inherit;
  }
  .swap-icon {
    transition: opacity 140ms ease;
  }
  .inline-comparison:hover .swap-icon,
  .inline-comparison:focus-visible .swap-icon {
    opacity: 1;
  }
  @media (prefers-reduced-motion: reduce) {
    .swap-icon {
      transition: none;
    }
  }
  .inline-comparison:hover {
    color: var(--accent);
    border-color: var(--accent);
  }
  .inline-comparison:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 4px;
  }
  .context-grid p:not(.context-number) {
    max-width: 42ch;
    line-height: 1.65;
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
