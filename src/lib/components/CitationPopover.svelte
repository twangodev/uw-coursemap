<script lang="ts">
  import PopoverSurface from "./PopoverSurface.svelte";
  import { Popover } from "bits-ui";
  import {
    X,
    ArrowUpRight,
    ChevronLeft,
    ChevronRight,
    MessageSquare,
    ChartColumn,
  } from "@lucide/svelte";
  import { getContext } from "svelte";
  import { citationContext, citationKey, citedReviews } from "$lib/citations";
  import { safeUrl, termName } from "$lib/format";
  import type { Citation } from "$lib/types";
  let {
    citations,
    reviewFiles,
    coursePath = "",
  }: {
    citations: Citation[];
    reviewFiles: string[];
    coursePath?: string;
  } = $props();
  const numberFor = getContext<((citation: Citation) => number) | undefined>(
    citationContext,
  );
  const sources = $derived(
    citations.filter(
      (citation, index) =>
        citations.findIndex(
          (other) => citationKey(other) === citationKey(citation),
        ) === index,
    ),
  );
  const numbers = $derived(
    sources.map((citation, index) => numberFor?.(citation) || index + 1),
  );
  const marker = $derived(
    numbers.length <= 3
      ? numbers.join(", ")
      : `${numbers.slice(0, 2).join(", ")}, +${numbers.length - 2}`,
  );
  let reviews = $state<any[]>([]);
  let loading = $state(false);
  let failure = $state("");
  let loaded = $state(false);
  let open = $state(false);
  let selected = $state(0);
  const current = $derived(Math.max(0, Math.min(selected, sources.length - 1)));
  const active = $derived(sources[current]);
  async function load() {
    if (
      loaded ||
      loading ||
      !sources.some((citation) => citation.type === "review")
    )
      return;
    loading = true;
    failure = "";
    try {
      reviews = await citedReviews(reviewFiles);
      loaded = true;
    } catch (error) {
      failure = (error as Error).message;
    } finally {
      loading = false;
    }
  }
</script>

<Popover.Root
  bind:open
  onOpenChange={(open) => {
    if (open) {
      selected = 0;
      load();
    }
  }}
>
  <Popover.Trigger
    class="inline ml-1 border-0 bg-transparent text-accent align-super font-sans text-[11px] leading-none whitespace-nowrap cursor-pointer rounded-[2px] citation-marker py-[3px] px-0.5"
    data-citation-trigger
    aria-label={`Show ${sources.length} ${sources.length === 1 ? "source" : "sources"}`}
  >
    [{marker}]
  </Popover.Trigger>

  <PopoverSurface
    width={380}
    padding="none"
    class="max-h-[min(520px,_var(--bits-popover-content-available-height))] overflow-hidden flex flex-col font-sans citation-preview"
    role="dialog"
    aria-label="Sources"
    sideOffset={10}
    collisionPadding={12}
  >
    <header
      class="shrink-0 flex justify-between items-center pr-3.5 pl-5 text-[12px] text-muted border-b border-b-border preview-heading py-2.5"
    >
      <span>Sources</span>
      <div class="flex items-center gap-0.5 preview-controls">
        {#if sources.length > 1}
          <span
            class="text-[11px] tabular-nums mr-2 source-position"
            aria-live="polite">{current + 1} / {sources.length}</span
          >
          <button
            class="grid place-items-center w-7 h-7 p-0 border-0 bg-transparent text-muted cursor-pointer rounded-[4px] source-nav"
            aria-label="Previous source"
            disabled={current === 0}
            onclick={() => (selected = current - 1)}
            ><ChevronLeft size={15} /></button
          >
          <button
            class="grid place-items-center w-7 h-7 p-0 border-0 bg-transparent text-muted cursor-pointer rounded-[4px] source-nav"
            aria-label="Next source"
            disabled={current === sources.length - 1}
            onclick={() => (selected = current + 1)}
            ><ChevronRight size={15} /></button
          >
        {/if}
        <Popover.Close
          class="grid place-items-center w-7 h-7 p-0 border-0 bg-transparent text-muted cursor-pointer rounded-[4px] citation-close"
          aria-label="Close sources"><X size={15} /></Popover.Close
        >
      </div>
    </header>
    {#if active}
      <article class="p-5 min-w-0 min-h-0 flex flex-col source-entry">
        <div
          class="flex items-center gap-1.5 text-muted text-[11px] shrink-0 source-origin"
        >
          {#if active.type === "review"}<MessageSquare
              size={13}
            />{:else}<ChartColumn size={13} />{/if}
          <span
            >{active.type === "review"
              ? "Rate My Professors"
              : "Madgrades"}</span
          >
          <span class="ml-auto tabular-nums source-number"
            >[{numbers[current]}]</span
          >
        </div>
        <h3
          class="text-[17px] font-medium mt-3 mb-0 leading-[1.35] wrap-anywhere shrink-0 mx-0"
        >
          {active.type === "review"
            ? active.instructor_name || "Student review"
            : active.course_id || "Grade record"}
        </h3>
        <p
          class="text-[11px] text-muted mt-[5px] mb-0 shrink-0 source-date mx-0"
        >
          {active.type === "review"
            ? active.review_date?.slice(0, 10) || "Date not recorded"
            : `${termName(active.term_id || "")}${active.section_number != null ? ` · Section ${active.section_number}` : ""}`}
        </p>
        <div
          class="min-h-0 mt-4.5 mb-5.5 max-h-60 overflow-auto overscroll-contain source-body mx-0"
        >
          {#if active.type === "review"}
            {@const review = reviews.find(
              (row) => row.source_review_id === active.source_review_id,
            )}
            {#if review}<blockquote
                class="m-0 text-[15px] leading-[1.7] whitespace-pre-line wrap-anywhere"
              >
                {review.comment}
              </blockquote>
            {:else if loading}<p
                class="text-[13px] leading-[1.65] text-muted m-0 source-status"
                role="status"
              >
                Loading original comment…
              </p>
            {:else if failure}<p
                class="text-[13px] leading-[1.65] text-muted m-0 source-status"
                role="alert"
              >
                {failure} <button onclick={load}>Retry</button>
              </p>
            {:else if loaded}<p
                class="text-[13px] leading-[1.65] text-muted m-0 source-status"
              >
                The original comment is not in this dataset snapshot.
              </p>{/if}
          {:else}<p
              class="text-[13px] leading-[1.65] text-muted m-0 source-status"
            >
              Recorded grade distribution for this term{active.section_number !=
              null
                ? " and section"
                : ""}.
            </p>{/if}
        </div>
        <footer class="flex items-center justify-between gap-3 shrink-0">
          {#if active.type === "review"}
            {#if safeUrl(active.source_url)}<a
                class="inline-flex items-center gap-1 text-[11px]"
                href={safeUrl(active.source_url)}
                target="_blank"
                rel="noreferrer">View RMP profile <ArrowUpRight size={13} /></a
              >{/if}
          {:else}<a
              class="inline-flex items-center gap-1 text-[11px]"
              href={`${coursePath}#grades`}
              onclick={() => (open = false)}
              >View grade history <ArrowUpRight size={13} /></a
            >{/if}
          <a
            class="inline-flex items-center gap-1 text-[11px] text-muted ml-auto all-sources"
            href={`${coursePath}#evidence`}
            onclick={() => (open = false)}>All sources</a
          >
        </footer>
      </article>
    {/if}
  </PopoverSurface>
</Popover.Root>
<noscript><a href={`${coursePath}#evidence`}>Sources</a></noscript>

<style>
  :global(.citation-marker:hover) {
    background: var(--accent-soft);
  }
  :global(.citation-marker:focus-visible) {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .source-nav:hover:not(:disabled),
  :global(.citation-close:hover) {
    background: var(--accent-soft);
    color: var(--accent);
  }
  .source-nav:disabled {
    opacity: 0.3;
    cursor: default;
  }
  .source-body {
    scrollbar-width: thin;
  }
  @media (prefers-reduced-motion: no-preference) {
    :global(.citation-preview[data-state="open"]) {
      animation: source-enter 140ms ease-out;
    }
    @keyframes source-enter {
      from {
        opacity: 0;
        transform: translateY(3px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  }
</style>
