<script lang="ts">
  import { ArrowUpRight, Minus } from "@lucide/svelte";
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

<details class="stats-card" style={`--span:${span}`} bind:open>
  <summary>
    <div class="card-heading">
      <h2>{title}</h2>
      {#if open}<Minus size={18} strokeWidth={1.4} />{:else}<ArrowUpRight
          size={18}
          strokeWidth={1.4}
        />{/if}
    </div>
    {#if !open}<div class="card-preview">{@render preview()}</div>{/if}
  </summary>
  {#if open}<div class="card-body">{@render children()}</div>{/if}
</details>

<style>
  .stats-card {
    grid-column: span var(--span);
    min-width: 0;
    background: color-mix(in srgb, var(--surface) 55%, var(--bg));
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: clip;
    transition:
      border-color 180ms ease,
      background 180ms ease;
  }
  .stats-card[open] {
    grid-column: 1 / -1;
  }
  .stats-card:hover {
    border-color: color-mix(in srgb, var(--muted) 50%, var(--border));
  }
  summary {
    display: block;
    list-style: none;
    cursor: pointer;
    padding: 28px;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  summary:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: -3px;
    border-radius: 12px;
  }
  .card-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }
  h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 450;
    letter-spacing: -0.025em;
    color: var(--text);
  }
  .card-heading :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
    transition:
      transform 180ms ease,
      color 180ms ease;
  }
  summary:hover .card-heading :global(svg) {
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
  .card-body {
    padding: 4px 28px 30px;
    animation: enter 180ms ease-out;
  }
  @keyframes enter {
    from {
      opacity: 0;
      transform: translateY(5px);
    }
    to {
      opacity: 1;
      transform: none;
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
    summary {
      padding: 22px;
    }
    .card-preview {
      height: 220px;
    }
    .card-body {
      padding: 4px 22px 24px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .stats-card,
    .card-heading :global(svg) {
      transition: none;
    }
    .card-body {
      animation: none;
    }
  }
</style>
