<script lang="ts">
  import { Dialog } from "bits-ui";
  import { ArrowUpRight, X } from "@lucide/svelte";
  import type { Snippet } from "svelte";
  let {
    title,
    compact = false,
    span = 4,
    preview,
    children,
  }: {
    title: string;
    compact?: boolean;
    span?: number;
    preview: Snippet;
    children: Snippet;
  } = $props();
  let open = $state(false);
</script>

<div
  class="[grid-column:span_var(--span)] min-w-0 bg-[color-mix(in_srgb,_var(--surface)_55%,_var(--bg))] border border-border rounded-[12px] overflow-clip stats-card"
  class:compact
  style={`--span:${span}`}
>
  <Dialog.Root bind:open>
    <Dialog.Trigger
      class="block w-full text-left bg-transparent border-0 text-foreground cursor-pointer p-7 stats-card-trigger"
      aria-label={title}
    >
      <span
        class="flex items-center justify-between gap-4 text-[16px] font-[450] tracking-[-0.025em] card-heading"
        ><span role="heading" aria-level="2">{title}</span><ArrowUpRight
          size={18}
          strokeWidth={1.4}
        /></span
      >
      <div
        class="h-60 pt-7 flex flex-col justify-center pointer-events-none card-preview"
      >
        {@render preview()}
      </div>
    </Dialog.Trigger>
    <Dialog.Portal>
      <Dialog.Overlay
        class="fixed inset-0 z-70 bg-[#0008] stats-dialog-overlay"
      />
      <Dialog.Content
        class="fixed z-80 top-1/2 left-1/2 w-[min(1160px,_calc(100vw_-_48px))] max-h-[calc(100dvh_-_48px)] overflow-auto bg-canvas text-foreground border border-border rounded-[12px] shadow-[0_24px_100px_#0005] stats-dialog"
      >
        <div
          class="sticky top-0 z-2 flex items-center justify-between gap-6 bg-canvas border-b border-b-border dialog-heading py-5.5 px-7"
        >
          <Dialog.Title
            class="m-0 text-[20px] font-[450] tracking-[-0.03em] stats-dialog-title"
            >{title}</Dialog.Title
          ><Dialog.Close
            class="grid place-items-center w-8 h-8 p-0 border-0 rounded-control bg-surface text-muted cursor-pointer stats-dialog-close"
            aria-label="Close statistics"
            ><X size={20} strokeWidth={1.5} /></Dialog.Close
          >
        </div>
        <div class="p-7 card-body">{@render children()}</div>
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
</div>

<style>
  .stats-card {
    transition: border-color 180ms ease;
  }
  .stats-card:hover {
    border-color: color-mix(in srgb, var(--muted) 50%, var(--border));
  }
  :global(.stats-card-trigger) {
    font: inherit;
  }
  :global(.stats-card-trigger:focus-visible) {
    outline: 2px solid var(--accent);
    outline-offset: -3px;
    border-radius: 12px;
  }
  .card-heading :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
    transition:
      transform 180ms ease,
      color 180ms ease;
  }
  :global(.stats-card-trigger:hover) .card-heading :global(svg) {
    transform: translate(2px, -2px);
    color: var(--accent);
  }
  :global(.stats-dialog-overlay) {
    backdrop-filter: blur(4px);
    animation: overlay-in 160ms ease-out;
  }
  :global(.stats-dialog) {
    transform: translate(-50%, -50%);
    animation: dialog-in 180ms ease-out;
  }
  @keyframes overlay-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes dialog-in {
    from {
      opacity: 0;
      transform: translate(-50%, calc(-50% + 6px));
    }
    to {
      opacity: 1;
      transform: translate(-50%, -50%);
    }
  }
  @media (max-width: 900px) {
    .stats-card {
      grid-column: span 6;
    }
  }
  @media (max-width: 600px) {
    .stats-card {
      grid-column: 1 / -1;
    }
    :global(.stats-card-trigger) {
      padding: 22px;
    }
    .card-preview {
      height: 220px;
    }
    :global(.stats-dialog) {
      width: calc(100vw - 20px);
      max-height: calc(100dvh - 20px);
    }
    .dialog-heading,
    .card-body {
      padding: 20px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .stats-card,
    .card-heading :global(svg) {
      transition: none;
    }
    :global(.stats-dialog),
    :global(.stats-dialog-overlay) {
      animation: none;
    }
  }
  @media (max-width: 760px) {
    .compact .card-preview {
      height: 165px;
    }
  }
</style>
