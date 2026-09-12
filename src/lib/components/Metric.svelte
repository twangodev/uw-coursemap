<script lang="ts">
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import MetricComparison from "./MetricComparison.svelte";
  let {
    value,
    label,
    decimals = 0,
    suffix = "",
    reference,
    kind = "number",
    group,
    tone,
    labelFirst = false,
  }: {
    value: number | null | undefined;
    label: string;
    decimals?: number;
    suffix?: string;
    reference?: number | null;
    kind?: "gpa" | "share" | "number";
    group?: string;
    tone?: string;
    labelFirst?: boolean;
  } = $props();
</script>

<div class="metric" class:label-first={labelFirst}>
  <strong style:color={tone}>
    {#if reference != null}
      <MetricComparison value={value ?? null} {reference} {kind} {label} {group}
        ><AnimatedNumber {value} {decimals} {suffix} /></MetricComparison
      >
    {:else}<AnimatedNumber {value} {decimals} {suffix} />{/if}
  </strong>
  <span class="label">{label}</span>
</div>

<style>
  .metric {
    display: flex;
    flex-direction: column;
    gap: 7px;
    min-width: 0;
  }
  strong {
    font-size: var(--metric-size, 28px);
    font-weight: 500;
    letter-spacing: -0.04em;
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
  }
  .label {
    color: var(--muted);
    font-size: 13px;
  }
  .label-first .label {
    order: -1;
  }
</style>
