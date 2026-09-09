<script lang="ts">
  import NumberFlow from "@number-flow/svelte";
  let { value, decimals = 0, suffix }: {
    value: number | null | undefined;
    decimals?: number;
    suffix?: string;
  } = $props();
</script>

{#if value != null && Number.isFinite(value)}
  <span role="img" aria-label={new Intl.NumberFormat("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value) + (suffix || "")}><NumberFlow
    aria-hidden="true"
    {value}
    {suffix}
    locales="en-US"
    format={{ minimumFractionDigits: decimals, maximumFractionDigits: decimals }}
    transformTiming={{ duration: 320, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }}
    opacityTiming={{ duration: 180, easing: "ease-out" }}
    respectMotionPreference={true}
    style="font-variant-numeric: tabular-nums; --number-flow-mask-height: 0.08em;"
  /></span>
{:else}—{/if}
