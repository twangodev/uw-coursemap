<script lang="ts">
  import { Plus, Minus } from "@lucide/svelte";
  import type { Snippet } from "svelte";
  let {
    title,
    variant = "section",
    lazy = true,
    class: className = "",
    description,
    children,
  }: {
    title: string;
    description?: string;
    children: Snippet;
    variant?: "section" | "compact";
    lazy?: boolean;
    class?: string;
  } = $props();
  let open = $state(false);
</script>

<details
  class={`border-t border-t-border p-0 disclosure ${className}`}
  class:compact={variant === "compact"}
  bind:open
>
  <summary
    class="list-none flex justify-between gap-6 items-center text-foreground cursor-pointer text-[17px] font-[450] py-6 px-0"
    ><span class="flex flex-wrap items-baseline gap-y-2 gap-x-6"
      >{title}{#if description}<small class="text-[12px] font-normal text-muted"
          >{description}</small
        >{/if}</span
    >{#if open}<Minus size={17} strokeWidth={1.4} />{:else}<Plus
        size={17}
        strokeWidth={1.4}
      />{/if}</summary
  >
  {#if open || !lazy}<div class="pt-2 pb-9 disclosure-body px-0">
      {@render children()}
    </div>{/if}
</details>

<style>
  summary::-webkit-details-marker {
    display: none;
  }
  summary :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
  }
  summary:hover {
    color: var(--accent);
  }
  .disclosure-body {
    animation: reveal 180ms ease-out;
  }
  .compact summary {
    padding: 12px 0;
    font-size: 13px;
  }
  .compact .disclosure-body {
    padding: 0 0 16px;
    font-size: 13px;
    line-height: 1.65;
    margin-top: 0;
  }
  .compact .disclosure-body > :global(p) {
    max-width: none;
  }
  .compact :global(p + p) {
    margin-top: 12px;
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
