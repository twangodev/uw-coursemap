<script lang="ts">
  import { Popover } from "bits-ui";
  import { X, ArrowUpRight } from "@lucide/svelte";
  import { getContext } from "svelte";
  import { citationContext, citationKey, citedReviews } from "$lib/citations";
  import { safeUrl, termName } from "$lib/format";
  import type { Citation } from "$lib/types";
  let { citations, reviewFiles }: { citations: Citation[]; reviewFiles: string[] } = $props();
  const numberFor = getContext<((citation: Citation) => number) | undefined>(citationContext);
  const sources = $derived(citations.filter((citation, index) => citations.findIndex((other) => citationKey(other) === citationKey(citation)) === index));
  const numbers = $derived(sources.map((citation, index) => numberFor?.(citation) || index + 1));
  const marker = $derived(numbers.length <= 3 ? numbers.join(", ") : `${numbers.slice(0, 2).join(", ")}, +${numbers.length - 2}`);
  let reviews = $state<any[]>([]);
  let loading = $state(false);
  let failure = $state("");
  let loaded = $state(false);
  let open = $state(false);
  async function load() {
    if (loaded || loading || !sources.some((citation) => citation.type === "review")) return;
    loading = true;
    failure = "";
    try { reviews = await citedReviews(reviewFiles); loaded = true; }
    catch (error) { failure = (error as Error).message; }
    finally { loading = false; }
  }
</script>

<Popover.Root bind:open onOpenChange={(open) => { if (open) load(); }}>
  <Popover.Trigger class="citation-marker" data-citation-trigger aria-label={`Show ${sources.length} ${sources.length === 1 ? "source" : "sources"}`}>
    [{marker}]
  </Popover.Trigger>
  <Popover.Portal>
    <Popover.Content class="citation-preview" role="dialog" aria-label="Sources" sideOffset={10} collisionPadding={12}>
      <div class="preview-heading"><span>Sources</span><Popover.Close class="citation-close" aria-label="Close sources"><X size={16} /></Popover.Close></div>
      <div class="source-list">
        {#if loading}<p class="source-status" role="status">Loading original comments…</p>{/if}
        {#if failure}<p class="source-status" role="alert">{failure} <button onclick={load}>Retry</button></p>{/if}
        {#each sources as citation, index}
          <article class="source-entry">
            <h3><span class="source-number">{numbers[index]}</span> {citation.type === "review" ? citation.instructor_name || "Student review" : citation.course_id || "Grade record"}</h3>
            <p class="source-date">{citation.type === "review" ? `${citation.review_date?.slice(0, 10) || "Undated"} · Rate My Professors` : `${termName(citation.term_id || "")} · Madgrades${citation.section_number != null ? ` · Section ${citation.section_number}` : ""}`}</p>
            {#if citation.type === "review"}
              {@const review = reviews.find((row) => row.source_review_id === citation.source_review_id)}
              {#if review}<blockquote>{review.comment}</blockquote>
              {:else if loaded}<p class="source-status">The original comment is not in this dataset snapshot.</p>{/if}
              {#if safeUrl(citation.source_url)}<a href={safeUrl(citation.source_url)} target="_blank" rel="noreferrer">View RMP profile <ArrowUpRight size={13} /></a>{/if}
            {:else}<p class="source-status">Recorded grade distribution for this term{citation.section_number != null ? " and section" : ""}.</p><a href="#grades" onclick={() => open = false}>View grade history <ArrowUpRight size={13} /></a>{/if}
          </article>
        {/each}
      </div>
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>
<noscript><a href="#evidence">Sources</a></noscript>

<style>
  :global(.citation-marker) { display: inline; padding: 3px 2px; margin-left: 4px; border: 0; background: none; color: var(--accent); font: 11px var(--font-sans); vertical-align: super; line-height: 1; white-space: nowrap; cursor: pointer; border-radius: 2px; }
  :global(.citation-marker:hover) { background: var(--accent-soft); }
  :global(.citation-marker:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
  :global(.citation-preview) { z-index: 100; width: min(400px, calc(100vw - 24px)); max-height: min(480px, var(--bits-popover-content-available-height)); overflow: auto; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 10px 35px #0002; padding: 18px 20px; }
  .preview-heading { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--muted); margin-bottom: 16px; }
  :global(.citation-close) { display: grid; place-items: center; padding: 5px; border: 0; background: none; color: var(--muted); cursor: pointer; border-radius: 3px; }
  .source-entry + .source-entry { border-top: 1px solid var(--border); padding-top: 18px; margin-top: 18px; }
  h3 { font-size: 14px; font-weight: 500; margin: 0; }
  .source-number { color: var(--muted); font-size: 11px; margin-right: 5px; }
  .source-date { font-size: 11px; color: var(--muted); margin-top: 5px; }
  blockquote { margin: 14px 0; font-size: 14px; line-height: 1.7; white-space: pre-line; overflow-wrap: anywhere; }
  .source-entry a { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; margin-top: 8px; }
  .source-status { font-size: 12px; line-height: 1.6; color: var(--muted); margin-top: 10px; }
</style>
