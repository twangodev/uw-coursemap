<script lang="ts">
  import { Popover } from "bits-ui";
  import { X, ArrowUpRight, ChevronLeft, ChevronRight, MessageSquare, ChartColumn } from "@lucide/svelte";
  import { getContext } from "svelte";
  import { citationContext, citationKey, citedReviews } from "$lib/citations";
  import { safeUrl, termName } from "$lib/format";
  import type { Citation } from "$lib/types";
  let { citations, reviewFiles, coursePath = "" }: { citations: Citation[]; reviewFiles: string[]; coursePath?: string } = $props();
  const numberFor = getContext<((citation: Citation) => number) | undefined>(citationContext);
  const sources = $derived(citations.filter((citation, index) => citations.findIndex((other) => citationKey(other) === citationKey(citation)) === index));
  const numbers = $derived(sources.map((citation, index) => numberFor?.(citation) || index + 1));
  const marker = $derived(numbers.length <= 3 ? numbers.join(", ") : `${numbers.slice(0, 2).join(", ")}, +${numbers.length - 2}`);
  let reviews = $state<any[]>([]);
  let loading = $state(false);
  let failure = $state("");
  let loaded = $state(false);
  let open = $state(false);
  let selected = $state(0);
  const current = $derived(Math.max(0, Math.min(selected, sources.length - 1)));
  const active = $derived(sources[current]);
  async function load() {
    if (loaded || loading || !sources.some((citation) => citation.type === "review")) return;
    loading = true;
    failure = "";
    try { reviews = await citedReviews(reviewFiles); loaded = true; }
    catch (error) { failure = (error as Error).message; }
    finally { loading = false; }
  }
</script>

<Popover.Root bind:open onOpenChange={(open) => { if (open) { selected = 0; load(); } }}>
  <Popover.Trigger class="citation-marker" data-citation-trigger aria-label={`Show ${sources.length} ${sources.length === 1 ? "source" : "sources"}`}>
    [{marker}]
  </Popover.Trigger>
  <Popover.Portal>
    <Popover.Content class="citation-preview" role="dialog" aria-label="Sources" sideOffset={10} collisionPadding={12}>
      <header class="preview-heading">
        <span>Sources</span>
        <div class="preview-controls">
          {#if sources.length > 1}
            <span class="source-position" aria-live="polite">{current + 1} / {sources.length}</span>
            <button class="source-nav" aria-label="Previous source" disabled={current === 0} onclick={() => selected = current - 1}><ChevronLeft size={15} /></button>
            <button class="source-nav" aria-label="Next source" disabled={current === sources.length - 1} onclick={() => selected = current + 1}><ChevronRight size={15} /></button>
          {/if}
          <Popover.Close class="citation-close" aria-label="Close sources"><X size={15} /></Popover.Close>
        </div>
      </header>
      {#if active}
        <article class="source-entry">
          <div class="source-origin">
            {#if active.type === "review"}<MessageSquare size={13} />{:else}<ChartColumn size={13} />{/if}
            <span>{active.type === "review" ? "Rate My Professors" : "Madgrades"}</span>
            <span class="source-number">[{numbers[current]}]</span>
          </div>
          <h3>{active.type === "review" ? active.instructor_name || "Student review" : active.course_id || "Grade record"}</h3>
          <p class="source-date">{active.type === "review" ? active.review_date?.slice(0, 10) || "Date not recorded" : `${termName(active.term_id || "")}${active.section_number != null ? ` · Section ${active.section_number}` : ""}`}</p>
          <div class="source-body">
            {#if active.type === "review"}
              {@const review = reviews.find((row) => row.source_review_id === active.source_review_id)}
              {#if review}<blockquote>{review.comment}</blockquote>
              {:else if loading}<p class="source-status" role="status">Loading original comment…</p>
              {:else if failure}<p class="source-status" role="alert">{failure} <button onclick={load}>Retry</button></p>
              {:else if loaded}<p class="source-status">The original comment is not in this dataset snapshot.</p>{/if}
            {:else}<p class="source-status">Recorded grade distribution for this term{active.section_number != null ? " and section" : ""}.</p>{/if}
          </div>
          <footer>
            {#if active.type === "review"}
              {#if safeUrl(active.source_url)}<a href={safeUrl(active.source_url)} target="_blank" rel="noreferrer">View RMP profile <ArrowUpRight size={13} /></a>{/if}
            {:else}<a href={`${coursePath}#grades`} onclick={() => open = false}>View grade history <ArrowUpRight size={13} /></a>{/if}
            <a class="all-sources" href={`${coursePath}#evidence`} onclick={() => open = false}>All sources</a>
          </footer>
        </article>
      {/if}
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>
<noscript><a href={`${coursePath}#evidence`}>Sources</a></noscript>

<style>
  :global(.citation-marker) { display: inline; padding: 3px 2px; margin-left: 4px; border: 0; background: none; color: var(--accent); font: 11px var(--font-sans); vertical-align: super; line-height: 1; white-space: nowrap; cursor: pointer; border-radius: 2px; }
  :global(.citation-marker:hover) { background: var(--accent-soft); }
  :global(.citation-marker:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
  :global(.citation-preview) { z-index: 100; width: min(380px, calc(100vw - 24px)); max-height: min(520px, var(--bits-popover-content-available-height)); overflow: hidden; display: flex; flex-direction: column; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 12px 40px #0002; font-family: var(--font-sans); }
  .preview-heading { flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; padding: 10px 14px 10px 20px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--border); }
  .preview-controls { display: flex; align-items: center; gap: 2px; }
  .source-position { font-size: 11px; font-variant-numeric: tabular-nums; margin-right: 8px; }
  .source-nav, :global(.citation-close) { display: grid; place-items: center; width: 28px; height: 28px; padding: 0; border: 0; background: none; color: var(--muted); cursor: pointer; border-radius: 4px; }
  .source-nav:hover:not(:disabled), :global(.citation-close:hover) { background: var(--accent-soft); color: var(--accent); }
  .source-nav:disabled { opacity: .3; cursor: default; }
  .source-entry { padding: 20px; min-width: 0; min-height: 0; display: flex; flex-direction: column; }
  .source-origin { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: 11px; }
  .source-number { margin-left: auto; font-variant-numeric: tabular-nums; }
  h3 { font-size: 17px; font-weight: 500; margin: 12px 0 0; line-height: 1.35; overflow-wrap: anywhere; }
  .source-date { font-size: 11px; color: var(--muted); margin: 5px 0 0; }
  .source-body { min-height: 0; margin: 18px 0 22px; max-height: 240px; overflow: auto; overscroll-behavior: contain; scrollbar-width: thin; }
  blockquote { margin: 0; font-size: 15px; line-height: 1.7; white-space: pre-line; overflow-wrap: anywhere; }
  footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  footer a { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; }
  .all-sources { color: var(--muted); margin-left: auto; }
  .source-origin, h3, .source-date, footer { flex-shrink: 0; }
  .source-status { font-size: 13px; line-height: 1.65; color: var(--muted); margin: 0; }
  @media (prefers-reduced-motion: no-preference) {
    :global(.citation-preview[data-state="open"]) { animation: source-enter 140ms ease-out; }
    @keyframes source-enter { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
  }
</style>
