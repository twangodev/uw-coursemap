<script lang="ts">
  import type { InstructorRatings } from "$lib/view-models";
  import Disclosure from "./Disclosure.svelte";
  import Metric from "./Metric.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import MetricComparison from "./MetricComparison.svelte";
  import { metricColor, type Benchmark } from "$lib/grade-benchmarks";
  import { safeUrl, termName } from "$lib/format";
  let {
    ratings,
    grades,
    courseUid,
    benchmark,
    group = "UW–Madison",
    term = "",
  }: { ratings?: InstructorRatings | null; grades?: { gpa: number; graded: number; sections: number } | null; courseUid?: string; benchmark?: Benchmark | null; group?: string; term?: string } = $props();
  let course = $derived(courseUid ? ratings?.courses?.[courseUid] : null);
</script>

{#if ratings || grades}
  <div class="instructor-stats">
    {#if ratings}<div class="rating-values">
        <Metric value={ratings.bayesian_quality} label="Adjusted rating" decimals={1} suffix="/5" tone={ratings.bayesian_quality != null && ratings.bayesian_quality >= 4 ? "var(--positive)" : ratings.bayesian_quality != null && ratings.bayesian_quality < 3 ? "var(--negative)" : undefined} />
        <Metric value={ratings.difficulty} label="RMP difficulty" decimals={1} suffix="/5" />
        <Metric value={ratings.review_count} label="captured reviews" />
      </div>
      {#if ratings.bayesian_quality != null}<Disclosure title="About this rating" variant="compact" lazy={false} class="rating-method"><p>Raw average: {ratings.quality?.toFixed(2)}/5 from {ratings.quality_count} quality ratings. The adjusted rating blends this with the UW review average ({ratings.prior_mean?.toFixed(2)}/5), weighted as {ratings.prior_weight} additional ratings. Smaller samples stay closer to that average. Each captured review is counted once in the prior; this does not correct who chooses to leave a review.</p></Disclosure>{/if}
      {#if course && course.review_count !== ratings.review_count}<p
          class="course-rating"
        >
          For this course: <strong
            >{course.quality?.toFixed(1) ?? "—"}/5 raw quality</strong
          >
          · {course.difficulty?.toFixed(1) ?? "—"}/5 difficulty · {course.review_count}
          reviews
        </p>{/if}
      <p class="rating-source">
        <a href={safeUrl(ratings.source_url)} target="_blank" rel="noreferrer"
          >RMP profile ↗</a
        > · All captured review dates; profile matched by name.
      </p>
    {/if}
    {#if grades?.graded}<div class="teaching-grades">
        <strong style:color={metricColor(grades.gpa, benchmark?.gpa)}><MetricComparison value={grades.gpa} reference={benchmark?.gpa} kind="gpa" label="Instructor course GPA" {group}><AnimatedNumber value={grades.gpa} decimals={2} /></MetricComparison></strong> average GPA · <AnimatedNumber value={grades.graded} />
        letter grades across <AnimatedNumber value={grades.sections} /> recorded sections
        {#if courseUid}<span class="grade-coverage">This course · {term ? termName(term) : "all recorded terms"}. Comparison uses whole-course averages.</span>{/if}
      </div>{/if}
  </div>
{/if}

<style>
  .grade-coverage { display: block; color: var(--muted); font-size: 12px; margin-top: 6px; }
  .instructor-stats {
    margin: 12px 0 24px;
  }
  .rating-values {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
  }
  .course-rating {
    margin-top: 20px;
    font-size: 13px;
    line-height: 1.7;
  }
  .rating-source {
    font-size: 12px;
    color: var(--muted);
    margin-top: 12px;
  }
  .teaching-grades {
    margin-top: 20px;
    font-size: 14px;
    color: var(--muted);
    line-height: 1.7;
  }
  .teaching-grades strong {
    color: var(--text);
  }
  @media (max-width: 640px) {
    .rating-values {
      gap: 24px;
    }
  }
</style>
