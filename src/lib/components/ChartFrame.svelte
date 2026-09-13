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

<section class="min-w-0 chart-frame" aria-label={title}>
  <div class="mb-4 chart-heading">
    <h3 class="text-[17px] font-medium">{title}</h3>
    {#if period}<p class="text-[12px] leading-[1.65] text-muted mt-[5px]">
        {period}
      </p>{/if}
  </div>
  {#if empty}<p class="empty">{emptyLabel}</p>{:else}{@render children()}{/if}
  {#if note}<div
      class="text-[12px] leading-[1.65] text-muted mt-4.5 chart-note"
    >
      {@render note()}
    </div>{/if}
</section>
