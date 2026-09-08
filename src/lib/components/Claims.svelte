<script lang="ts">
  import type { Claim } from "$lib/types";
  import { safeUrl, termName } from "$lib/format";
  let {
    claims = [],
    reviewFiles = [],
  }: { claims: Claim[]; reviewFiles?: string[] } = $props();
  let reviews = $state<any[]>([]);
  let loaded = $state(false);
  let failure = $state("");
  async function loadReviews() {
    if (loaded) return;
    try {
      reviews = (
        await Promise.all(
          reviewFiles.map(async (u) => {
            const r = await fetch(u);
            if (!r.ok)
              throw new Error(
                "Evidence unavailable. Reload to check for a dataset update.",
              );
            return r.json();
          }),
        )
      ).flat();
      loaded = true;
    } catch (e) {
      failure = (e as Error).message;
    }
  }
</script>

<div class="stack">
  {#each claims as claim}<div class="claim">
      <p>{claim.text}</p>
      {#if claim.citations?.length}<details
          class="citations"
          ontoggle={(e) => {
            if (e.currentTarget.open) loadReviews();
          }}
        >
          <summary>{claim.citations.length} sources</summary>
          <div class="stack">
            {#each claim.citations as c}<div>
                <p>
                  {c.type === "review"
                    ? `${c.instructor_name || "Instructor"} · ${c.review_date?.slice(0, 10) || "Undated review"}`
                    : `Grade record · ${termName(c.term_id || "")}`}
                </p>
                {#if c.type === "review"}{@const review = reviews.find(
                    (r) => r.source_review_id === c.source_review_id,
                  )}{#if review}<blockquote>
                      {review.comment}
                    </blockquote>{:else if failure}<p>
                      {failure}
                    </p>{/if}{#if safeUrl(c.source_url)}<a
                      href={safeUrl(c.source_url)}
                      target="_blank"
                      rel="noreferrer">Original source ↗</a
                    >{/if}{:else}<a href="#grades">View grade history ↓</a>{/if}
                <details>
                  <summary>Source record</summary>
                  <pre>{JSON.stringify(c, null, 2)}</pre>
                </details>
              </div>{/each}
          </div>
        </details>{/if}
    </div>{/each}
</div>

<style>
  .citations {
    border: 0;
    padding: 0.35rem 0;
  }
  blockquote {
    border-left: 2px solid var(--border);
    margin: 0.5rem 0;
    padding-left: 1rem;
    font-size: 0.95rem;
  }
</style>
