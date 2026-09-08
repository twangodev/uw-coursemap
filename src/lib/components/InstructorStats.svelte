<script lang="ts">
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
  }: { ratings?: any; grades?: any; courseUid?: string; benchmark?: Benchmark | null; group?: string; term?: string } = $props();
  let course = $derived(courseUid ? ratings?.courses?.[courseUid] : null);
</script>

{#if ratings || grades}
  <div class="instructor-stats">
    {#if ratings}<div class="rating-values">
        <div>
          <strong
            class:positive={ratings.quality >= 4}
            class:negative={ratings.quality != null && ratings.quality < 3}
            ><AnimatedNumber value={ratings.quality} decimals={1} /><small>/5</small></strong
          ><span>RMP quality</span>
        </div>
        <div>
          <strong
            ><AnimatedNumber value={ratings.difficulty} decimals={1} /><small>/5</small></strong
          ><span>RMP difficulty</span>
        </div>
        <div>
          <strong><AnimatedNumber value={ratings.review_count} /></strong><span
            >captured reviews</span
          >
        </div>
      </div>
      {#if course && course.review_count !== ratings.review_count}<p
          class="course-rating"
        >
          For this course: <strong
            >{course.quality?.toFixed(1) ?? "—"}/5 quality</strong
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
  .rating-values > div {
    display: grid;
    gap: 7px;
  }
  .rating-values strong {
    font-size: 28px;
    font-weight: 500;
    letter-spacing: -0.04em;
  }
  .rating-values small {
    font-size: 13px;
    font-weight: 400;
    color: var(--muted);
    margin-left: 3px;
  }
  .rating-values span {
    font-size: 13px;
    color: var(--muted);
  }
  .positive {
    color: var(--positive);
  }
  .negative {
    color: var(--negative);
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
