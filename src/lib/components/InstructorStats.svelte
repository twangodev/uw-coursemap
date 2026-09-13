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
  }: {
    ratings?: InstructorRatings | null;
    grades?: { gpa: number; graded: number; sections: number } | null;
    courseUid?: string;
    benchmark?: Benchmark | null;
    group?: string;
    term?: string;
  } = $props();
  let course = $derived(courseUid ? ratings?.courses?.[courseUid] : null);
</script>

{#if ratings || grades}
  <div class="mt-3 mb-6 instructor-stats mx-0">
    {#if ratings}<div class="flex gap-8 flex-wrap rating-values">
        <Metric
          value={ratings.bayesian_quality}
          label="Adjusted rating"
          decimals={1}
          suffix="/5"
          tone={ratings.bayesian_quality != null &&
          ratings.bayesian_quality >= 4
            ? "var(--positive)"
            : ratings.bayesian_quality != null && ratings.bayesian_quality < 3
              ? "var(--negative)"
              : undefined}
        />
        <Metric
          value={ratings.difficulty}
          label="RMP difficulty"
          decimals={1}
          suffix="/5"
        />
        <Metric value={ratings.review_count} label="captured reviews" />
      </div>
      {#if ratings.bayesian_quality != null}<Disclosure
          title="About this rating"
          variant="compact"
          lazy={false}
          class="rating-method"
          ><p>
            Raw average: {ratings.quality?.toFixed(2)}/5 from {ratings.quality_count}
            quality ratings. The adjusted rating blends this with the UW review average
            ({ratings.prior_mean?.toFixed(2)}/5), weighted as {ratings.prior_weight}
            additional ratings. Smaller samples stay closer to that average. Each
            captured review is counted once in the prior; this does not correct who
            chooses to leave a review.
          </p></Disclosure
        >{/if}
      {#if course && course.review_count !== ratings.review_count}<p
          class="mt-5 text-[13px] leading-[1.7] course-rating"
        >
          For this course: <strong
            >{course.quality?.toFixed(1) ?? "—"}/5 raw quality</strong
          >
          · {course.difficulty?.toFixed(1) ?? "—"}/5 difficulty · {course.review_count}
          reviews
        </p>{/if}
      <p class="text-[12px] text-muted mt-3 rating-source">
        <a href={safeUrl(ratings.source_url)} target="_blank" rel="noreferrer"
          >RMP profile ↗</a
        > · All captured review dates; profile matched by name.
      </p>
    {/if}
    {#if grades?.graded}<div
        class="mt-5 text-[14px] text-muted leading-[1.7] teaching-grades"
      >
        <strong
          class="text-foreground"
          style:color={metricColor(grades.gpa, benchmark?.gpa)}
          ><MetricComparison
            value={grades.gpa}
            reference={benchmark?.gpa}
            kind="gpa"
            label="Instructor course GPA"
            {group}
            ><AnimatedNumber
              value={grades.gpa}
              decimals={2}
            /></MetricComparison
          ></strong
        >
        average GPA · <AnimatedNumber value={grades.graded} />
        letter grades across <AnimatedNumber value={grades.sections} /> recorded sections
        {#if courseUid}<span
            class="block text-muted text-[12px] mt-1.5 grade-coverage"
            >This course · {term ? termName(term) : "all recorded terms"}.
            Comparison uses whole-course averages.</span
          >{/if}
      </div>{/if}
  </div>
{/if}

<style>
  @media (max-width: 640px) {
    .rating-values {
      gap: 24px;
    }
  }
</style>
