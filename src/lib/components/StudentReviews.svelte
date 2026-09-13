<script lang="ts">
  import type { ReviewPage } from "$lib/view-models";
  import { onDestroy } from "svelte";
  import Select from "./Select.svelte";
  import { safeUrl, courseUrl } from "$lib/format";
  let {
    initial,
    uid,
    revision,
  }: { initial: ReviewPage; uid: string; revision: string } = $props();
  let loaded = $state<ReviewPage | null>(null),
    selectedCourse = $state(""),
    loading = $state(false),
    failure = $state("");
  let result = $derived(loaded || initial);
  let controller: AbortController | undefined;
  onDestroy(() => controller?.abort());
  $effect(() => {
    initial;
    loaded = null;
    selectedCourse = "";
    controller?.abort();
  });
  async function load(course: string, more = false) {
    controller?.abort();
    const request = new AbortController();
    controller = request;
    selectedCourse = course;
    loading = true;
    failure = "";
    if (!more) loaded = { ...initial, items: [], total: 0, page: 0 };
    try {
      const query = new URLSearchParams({
        revision,
        page: String(more ? result.page + 1 : 1),
        course,
      });
      const response = await fetch(`/api/instructors/${uid}/reviews?${query}`, {
        signal: request.signal,
      });
      if (!response.ok)
        throw new Error(
          response.status === 409
            ? "Dataset updated. Reload this page."
            : "Reviews could not be loaded. Try again.",
        );
      const next = (await response.json()) as ReviewPage;
      if (!Array.isArray(next.items))
        throw new Error("Invalid review response. Try again.");
      if (!request.signal.aborted)
        loaded = {
          ...next,
          items: more ? [...result.items, ...next.items] : next.items,
        };
    } catch (e) {
      if (!request.signal.aborted) failure = (e as Error).message;
    } finally {
      if (controller === request) loading = false;
    }
  }
</script>

<section
  class="border-t border-t-border student-reviews py-8 px-0"
  aria-labelledby="reviews-heading"
>
  <div class="flex justify-between items-start gap-6 mb-7.5 review-heading">
    <div>
      <h2 class="text-[28px] font-medium mt-0 mb-2 mx-0" id="reviews-heading">
        What students say
      </h2>
      <p class="text-muted text-[12px]">
        Original student reviews · all captured dates
      </p>
    </div>
    <Select
      label="Reviews for course"
      value={selectedCourse}
      onChange={(v) => load(v)}
      options={[
        { value: "", label: "All courses" },
        ...initial.courses.map((c) => ({
          value: c.course_uid,
          label: c.course_id,
        })),
      ]}
    />
  </div>
  {#if failure}<p role="alert">
      {failure}
      <button onclick={() => load(selectedCourse, result.page > 0)}
        >Retry</button
      >
    </p>{/if}
  {#if loading}<p class="muted" role="status">Loading reviews…</p>{/if}
  <div class="grid grid-cols-[1fr_1fr] gap-x-12 review-list">
    {#each result.items as review (`${review.source_instructor_id}:${review.source_review_id}`)}
      {@const course = initial.courses.find(
        (c) => c.course_uid === review.course_uid,
      )}
      <article
        class="border-b border-b-border min-w-0 student-review py-6 px-0"
      >
        <div class="flex justify-between gap-5 text-[12px] review-meta">
          {#if course}<a href={courseUrl(course.course_id)}
              >{initial.courses.find((c) => c.course_uid === review.course_uid)
                ?.course_id ||
                review.course_label ||
                "Course"}</a
            >{:else}<span
              >{review.course_label
                ? `${review.course_label} · course not matched`
                : "Course not matched"}</span
            >{/if}<time class="text-muted"
            >{review.review_date?.slice(0, 10) || "Date unavailable"}</time
          >
        </div>
        <div class="flex gap-6 text-[12px] text-muted review-scores my-4 mx-0">
          {#if review.quality_rating != null}<span
              >Quality <strong
                class="text-foreground font-medium"
                class:positive={review.quality_rating >= 4}
                >{review.quality_rating}/5</strong
              ></span
            >{/if}{#if review.difficulty_rating != null}<span
              >Difficulty <strong class="text-foreground font-medium"
                >{review.difficulty_rating}/5</strong
              ></span
            >{/if}
        </div>
        {#if review.comment && review.comment.length > 350}<details class="m-0">
            <summary class="text-[15px] leading-[1.75] cursor-pointer"
              ><span class="text-foreground text-[15px] excerpt"
                >{review.comment.slice(0, 240)}…</span
              >
              <span class="text-accent text-[12px] read-more"
                >Read full review</span
              ><span class="text-accent text-[12px] read-less">Show less</span
              ></summary
            >
            <blockquote
              class="m-0 text-[15px] leading-[1.75] whitespace-pre-wrap wrap-anywhere"
            >
              {review.comment}
            </blockquote>
          </details>{:else}<blockquote
            class="m-0 text-[15px] leading-[1.75] whitespace-pre-wrap wrap-anywhere"
          >
            {review.comment || "This review contains ratings only."}
          </blockquote>{/if}
        {#if safeUrl(review.source_url)}<a
            class="inline-block mt-4.5 text-muted text-[11px] source"
            href={safeUrl(review.source_url)}
            target="_blank"
            rel="noreferrer">Rate My Professors ↗</a
          >{/if}
      </article>
    {:else}{#if !loading && !failure}<p class="muted">
          {initial.matched
            ? "No captured reviews for this selection."
            : "No unambiguous review-profile match is available."}
        </p>{/if}{/each}
  </div>
  {#if result.items.length < result.total}<button
      class="mt-6 bg-surface border border-border rounded-control text-foreground load-more py-2 px-4"
      disabled={loading}
      onclick={() => load(selectedCourse, true)}>Read more reviews</button
    >{/if}
  <p class="text-muted text-[12px] mt-6 leading-[1.7] review-note">
    Personal experiences, not a representative survey. Profile matching and
    captured coverage are shown in the source details.
  </p>
</section>

<style>
  .review-scores strong.positive {
    color: var(--positive);
  }
  summary span {
    display: block;
  }
  .read-less,
  details[open] summary .excerpt,
  details[open] summary .read-more {
    display: none;
  }
  details[open] summary .read-less {
    display: block;
  }
  @media (max-width: 700px) {
    .review-list {
      grid-template-columns: 1fr;
    }
    .review-heading {
      flex-direction: column;
    }
  }
</style>
