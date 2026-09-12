<script lang="ts">
  import InfoTooltip from "./InfoTooltip.svelte";
  import type { Snippet } from "svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  let { value, reference, kind = "number", label, group = "UW–Madison", children }: {
    value: number | null;
    reference: number | null | undefined;
    kind?: "gpa" | "share" | "number";
    label: string;
    group?: string;
    children: Snippet;
  } = $props();
  let open = $state(false);
  const difference = $derived(value != null && reference != null ? value - reference : null);
  const rounded = $derived(difference == null ? null : Number(difference.toFixed(kind === "gpa" ? 2 : kind === "share" ? 1 : 0)));
  const decimals = $derived(kind === "gpa" ? 2 : kind === "share" ? 1 : 0);
</script>

<InfoTooltip label={`${label} comparison`} bind:open contentClass="metric-tooltip" triggerClass="metric-tooltip-trigger">
  {#snippet trigger()}{@render children()}{/snippet}
        <p class="cohort">{group}</p>
        <p class="metric-comparison" class:above={rounded != null && rounded > 0} class:below={rounded != null && rounded < 0}>
          {#if rounded != null && reference != null}
            {rounded > 0 ? "↑" : rounded < 0 ? "↓" : "="} <AnimatedNumber value={Math.abs(rounded)} {decimals} />{kind === "share" ? " pp" : ""}
            <span>vs <AnimatedNumber value={reference} {decimals} />{kind === "share" ? "%" : ""}{kind === "number" ? " median" : " avg"}</span>
          {:else}<span>Comparison unavailable</span>{/if}
        </p>
</InfoTooltip>
<style>
  :global(.metric-tooltip-trigger) { border: 0; background: none; padding: 0; margin: 0; color: inherit; font: inherit; letter-spacing: inherit; cursor: help; border-radius: 3px; }
  :global(.metric-tooltip-trigger:focus-visible) { outline: 2px solid var(--accent); outline-offset: 5px; }
  .cohort { font-size: 11px; color: var(--muted); margin: 0 0 3px; }
  .metric-comparison { font-size: 13px; line-height: 1.7; margin: 0; color: var(--muted); font-variant-numeric: tabular-nums; }
  .above { color: var(--positive); }
  .below { color: var(--negative); }
  span { color: var(--muted); }
</style>
