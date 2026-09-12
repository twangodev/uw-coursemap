<script lang="ts">
  import { Dialog } from "bits-ui";
  import { ArrowUpRight, X } from "@lucide/svelte";
  import type { Snippet } from "svelte";
  let {
    title,
    span = 4,
    preview,
    children,
  }: {
    title: string;
    span?: number;
    preview: Snippet;
    children: Snippet;
  } = $props();
  let open = $state(false);
</script>

<div class="stats-card" style={`--span:${span}`}>
  <Dialog.Root bind:open>
    <Dialog.Trigger class="stats-card-trigger" aria-label={title}>
      <span class="card-heading"
        ><span role="heading" aria-level="2">{title}</span><ArrowUpRight
          size={18}
          strokeWidth={1.4}
        /></span
      >
      <div class="card-preview">{@render preview()}</div>
    </Dialog.Trigger>
    <Dialog.Portal>
      <Dialog.Overlay class="stats-dialog-overlay" />
      <Dialog.Content class="stats-dialog">
        <div class="dialog-heading">
          <Dialog.Title class="stats-dialog-title">{title}</Dialog.Title
          ><Dialog.Close
            class="stats-dialog-close"
            aria-label="Close statistics"
            ><X size={20} strokeWidth={1.5} /></Dialog.Close
          >
        </div>
        <div class="card-body">{@render children()}</div>
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
</div>

<style>
  .stats-card {
    grid-column: span var(--span);
    min-width: 0;
    background: color-mix(in srgb, var(--surface) 55%, var(--bg));
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: clip;
    transition: border-color 180ms ease;
  }
  .stats-card:hover {
    border-color: color-mix(in srgb, var(--muted) 50%, var(--border));
  }
  :global(.stats-card-trigger) {
    display: block;
    width: 100%;
    text-align: left;
    background: none;
    border: 0;
    color: var(--text);
    font: inherit;
    cursor: pointer;
    padding: 28px;
  }
  :global(.stats-card-trigger:focus-visible) {
    outline: 2px solid var(--accent);
    outline-offset: -3px;
    border-radius: 12px;
  }
  .card-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    font-size: 16px;
    font-weight: 450;
    letter-spacing: -0.025em;
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
  .card-preview {
    height: 240px;
    padding-top: 28px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    pointer-events: none;
  }
  :global(.stats-dialog-overlay) {
    position: fixed;
    inset: 0;
    z-index: 70;
    background: #0008;
    backdrop-filter: blur(4px);
    animation: overlay-in 160ms ease-out;
  }
  :global(.stats-dialog) {
    position: fixed;
    z-index: 80;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: min(1160px, calc(100vw - 48px));
    max-height: calc(100dvh - 48px);
    overflow: auto;
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 24px 100px #0005;
    animation: dialog-in 180ms ease-out;
  }
  .dialog-heading {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 22px 28px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
  }
  :global(.stats-dialog-title) {
    margin: 0;
    font-size: 20px;
    font-weight: 450;
    letter-spacing: -0.03em;
  }
  :global(.stats-dialog-close) {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    padding: 0;
    border: 0;
    border-radius: 5px;
    background: var(--surface);
    color: var(--muted);
    cursor: pointer;
  }
  .card-body {
    padding: 28px;
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
</style>
