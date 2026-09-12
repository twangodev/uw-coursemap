<script lang="ts">
  import { Tooltip } from "bits-ui";
  import { Info } from "@lucide/svelte";
  import type { Snippet } from "svelte";
  let {
    label,
    open = $bindable(false),
    children,
    trigger,
    contentClass = "info-tooltip",
    triggerClass = "info-trigger",
  }: {
    label: string;
    open?: boolean;
    children: Snippet;
    trigger?: Snippet;
    contentClass?: string;
    triggerClass?: string;
  } = $props();
</script>

<Tooltip.Provider delayDuration={150}>
  <Tooltip.Root bind:open disableCloseOnTriggerClick>
    <Tooltip.Trigger
      class={triggerClass}
      aria-label={label}
      onclick={() => (open = true)}
    >
      {#if trigger}{@render trigger()}{:else}<Info size={14} />{/if}
    </Tooltip.Trigger>
    <Tooltip.Portal>
      <Tooltip.Content
        class={`floating-surface ${contentClass}`}
        role="tooltip"
        sideOffset={8}
        collisionPadding={12}
      >
        {@render children()}
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>

<style>
  :global(.info-trigger) {
    display: inline-flex;
    align-items: center;
    padding: 2px;
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: help;
  }
</style>
