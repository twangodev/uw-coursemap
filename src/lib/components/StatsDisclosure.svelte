<script lang="ts">
  import { Plus, Minus } from "@lucide/svelte";
  import type { Snippet } from "svelte";
  let {
    title,
    description,
    children,
  }: { title: string; description?: string; children: Snippet } = $props();
  let open = $state(false);
</script>

<details class="stats-disclosure" bind:open>
  <summary
    ><span
      >{title}{#if description}<small>{description}</small>{/if}</span
    >{#if open}<Minus size={17} strokeWidth={1.4} />{:else}<Plus
        size={17}
        strokeWidth={1.4}
      />{/if}</summary
  >
  {#if open}<div class="disclosure-body">{@render children()}</div>{/if}
</details>

<style>
  .stats-disclosure {
    border-top: 1px solid var(--border);
  }
  summary {
    list-style: none;
    display: flex;
    justify-content: space-between;
    gap: 24px;
    align-items: center;
    padding: 24px 0;
    color: var(--text);
    cursor: pointer;
    font-size: 17px;
    font-weight: 450;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  summary > span {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px 24px;
  }
  summary small {
    font-size: 12px;
    font-weight: 400;
    color: var(--muted);
  }
  summary :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
  }
  summary:hover {
    color: var(--accent);
  }
  .disclosure-body {
    padding: 8px 0 36px;
    animation: reveal 180ms ease-out;
  }
  @keyframes reveal {
    from {
      opacity: 0;
      transform: translateY(5px);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .disclosure-body {
      animation: none;
    }
  }
</style>
