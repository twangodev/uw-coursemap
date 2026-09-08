<script lang="ts">
  import AnimatedNumber from "./AnimatedNumber.svelte";
  let { value, reference, kind = "number" }: {
    value: number | null;
    reference: number | null | undefined;
    kind?: "gpa" | "share" | "number";
  } = $props();
  const difference = $derived(value != null && reference != null ? value - reference : null);
  const rounded = $derived(difference == null ? null : Number(difference.toFixed(kind === "gpa" ? 2 : kind === "share" ? 1 : 0)));
  const decimals = $derived(kind === "gpa" ? 2 : kind === "share" ? 1 : 0);
</script>

<p class="metric-comparison" class:above={rounded != null && rounded > 0} class:below={rounded != null && rounded < 0}>
  {#if rounded != null && reference != null}
    {rounded > 0 ? "↑" : rounded < 0 ? "↓" : "="} <AnimatedNumber value={Math.abs(rounded)} {decimals} />{kind === "share" ? " pp" : ""}
    <span>vs <AnimatedNumber value={reference} {decimals} />{kind === "share" ? "%" : ""}{kind === "number" ? " median" : " avg"}</span>
  {:else}<span>Comparison unavailable</span>{/if}
</p>
<style>
  .metric-comparison { font-size: 12px; line-height: 1.7; margin: 10px 0 0; color: var(--muted); font-variant-numeric: tabular-nums; }
  .above { color: var(--positive); }
  .below { color: var(--negative); }
  span { color: var(--muted); }
</style>
