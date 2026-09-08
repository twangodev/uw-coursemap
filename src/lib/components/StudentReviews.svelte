<script lang="ts">
  import { onDestroy } from "svelte";
  import Select from "./Select.svelte";
  import { safeUrl, courseUrl } from "$lib/format";
  let {
    initial,
    uid,
    revision,
  }: { initial: any; uid: string; revision: string } = $props();
  let loaded = $state<any>(null),
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
      const next: any = await response.json();
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

<section class="student-reviews" aria-labelledby="reviews-heading">
  <div class="review-heading">
    <div>
      <h2 id="reviews-heading">What students say</h2>
      <p>Original student reviews · all captured dates</p>
    </div>
    <Select
      label="Reviews for course"
      value={selectedCourse}
      onChange={(v) => load(v)}
      options={[
        { value: "", label: "All courses" },
        ...initial.courses.map((c: any) => ({
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
  <div class="review-list">
    {#each result.items as review (`${review.source_instructor_id}:${review.source_review_id}`)}
      <article class="student-review">
        <div class="review-meta">
          {#if review.course_uid}<a href={courseUrl(review.course_uid, initial.courses.find((c: any) => c.course_uid === review.course_uid)?.course_id)}
              >{initial.courses.find(
                (c: any) => c.course_uid === review.course_uid,
              )?.course_id ||
                review.course_label ||
                "Course"}</a
            >{:else}<span
              >{review.course_label
                ? `${review.course_label} · course not matched`
                : "Course not matched"}</span
            >{/if}<time
            >{review.review_date?.slice(0, 10) || "Date unavailable"}</time
          >
        </div>
        <div class="review-scores">
          {#if review.quality_rating != null}<span
              >Quality <strong class:positive={review.quality_rating >= 4}
                >{review.quality_rating}/5</strong
              ></span
            >{/if}{#if review.difficulty_rating != null}<span
              >Difficulty <strong>{review.difficulty_rating}/5</strong></span
            >{/if}
        </div>
        {#if review.comment?.length > 350}<details>
            <summary
              ><span class="excerpt">{review.comment.slice(0, 240)}…</span>
              <span class="read-more">Read full review</span><span
                class="read-less">Show less</span
              ></summary
            >
            <blockquote>{review.comment}</blockquote>
          </details>{:else}<blockquote>
            {review.comment || "This review contains ratings only."}
          </blockquote>{/if}
        {#if safeUrl(review.source_url)}<a
            class="source"
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
      class="load-more"
      disabled={loading}
      onclick={() => load(selectedCourse, true)}>Read more reviews</button
    >{/if}
  <p class="review-note">
    Personal experiences, not a representative survey. Profile matching and
    captured coverage are shown in the source details.
  </p>
</section>

<style>
  .student-reviews {
    padding: 32px 0;
    border-top: 1px solid var(--border);
  }
  .review-heading {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 24px;
    margin-bottom: 30px;
  }
  .review-heading h2 {
    font-size: 28px;
    font-weight: 500;
    margin: 0 0 8px;
  }
  .review-heading p,
  .review-note {
    color: var(--muted);
    font-size: 12px;
  }
  .review-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 48px;
  }
  .student-review {
    padding: 24px 0;
    border-bottom: 1px solid var(--border);
    min-width: 0;
  }
  .review-meta {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    font-size: 12px;
  }
  .review-meta time {
    color: var(--muted);
  }
  .review-scores {
    display: flex;
    gap: 24px;
    font-size: 12px;
    margin: 16px 0;
    color: var(--muted);
  }
  .review-scores strong {
    color: var(--text);
    font-weight: 500;
  }
  .review-scores strong.positive {
    color: var(--positive);
  }
  blockquote {
    margin: 0;
    font-size: 15px;
    line-height: 1.75;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  .source {
    display: inline-block;
    margin-top: 18px;
    color: var(--muted);
    font-size: 11px;
  }
  details {
    margin: 0;
  }
  summary {
    font-size: 15px;
    line-height: 1.75;
    cursor: pointer;
  }
  summary span {
    display: block;
    color: var(--accent);
    font-size: 12px;
  }
  .read-less,
  details[open] summary .excerpt,
  details[open] summary .read-more {
    display: none;
  }
  details[open] summary .read-less {
    display: block;
  }
  summary .excerpt {
    color: var(--text);
    font-size: 15px;
  }
  .load-more {
    margin-top: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: 5px;
    color: var(--text);
  }
  .review-note {
    margin-top: 24px;
    line-height: 1.7;
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
