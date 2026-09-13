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
    variant = "default",
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
    variant?: "default" | "headline";
  } = $props();
</script>

<div
  class="flex flex-col gap-[7px] min-w-0 metric"
  class:label-first={labelFirst}
>
  <strong
    class={`font-medium tracking-[-0.04em] ${variant === "headline" ? "text-[clamp(28px,4vw,48px)]" : "text-[length:var(--metric-size,28px)] leading-[1.2] tabular-nums"}`}
    style:color={tone}
  >
    {#if reference != null}
      <MetricComparison value={value ?? null} {reference} {kind} {label} {group}
        ><AnimatedNumber {value} {decimals} {suffix} /></MetricComparison
      >
    {:else}<AnimatedNumber {value} {decimals} {suffix} />{/if}
  </strong>
  <span
    class={`text-muted text-[13px] ${labelFirst ? "-order-1" : ""} ${variant === "headline" ? "[@media(max-width:760px)]:text-[11px]" : ""}`}
    >{label}</span
  >
</div>
