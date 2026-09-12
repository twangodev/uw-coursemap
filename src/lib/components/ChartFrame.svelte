<script lang="ts">
  import type { Snippet } from "svelte";
  let {
    title,
    period,
    empty = false,
    emptyLabel = "No recorded data for this selection.",
    children,
    note,
  }: {
    title: string;
    period?: string;
    empty?: boolean;
    emptyLabel?: string;
    children: Snippet;
    note?: Snippet;
  } = $props();
</script>

<section class="chart-frame" aria-label={title}>
  <div class="chart-heading">
    <h3>{title}</h3>
    {#if period}<p>{period}</p>{/if}
  </div>
  {#if empty}<p class="empty">{emptyLabel}</p>{:else}{@render children()}{/if}
  {#if note}<div class="chart-note">{@render note()}</div>{/if}
</section>

<style>
  .chart-frame {
    min-width: 0;
  }
  .chart-heading {
    margin-bottom: 16px;
  }
  h3 {
    font-size: 17px;
    font-weight: 500;
  }
  .chart-heading p,
  .chart-note {
    font-size: 12px;
    line-height: 1.65;
    color: var(--muted);
  }
  .chart-heading p {
    margin-top: 5px;
  }
  .chart-note {
    margin-top: 18px;
  }
</style>
