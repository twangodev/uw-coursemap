<script lang="ts">
  import NumberFlow from "@number-flow/svelte";
  import { madisonZone, type CampusFact } from "$lib/campus";
  let { fact }: { fact: CampusFact } = $props();
  let parts = $derived(
    fact.at === undefined
      ? null
      : new Intl.DateTimeFormat("en-US", {
          timeZone: madisonZone,
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        }).formatToParts(fact.at),
  );
  let hour = $derived(
    Number(parts?.find((p) => p.type === "hour")?.value ?? 0),
  );
  let minute = $derived(
    Number(parts?.find((p) => p.type === "minute")?.value ?? 0),
  );
  let period = $derived(
    parts?.find((p) => p.type === "dayPeriod")?.value ?? "",
  );
  let label = $derived(
    typeof fact.value === "number"
      ? fact.value.toLocaleString("en-US") + (fact.suffix ?? "")
      : fact.value,
  );
  const transformTiming = {
    duration: 400,
    easing: "cubic-bezier(0.22, 1, 0.36, 1)",
  };
</script>

<span
  class="inline-flex items-baseline tabular-nums value"
  role="img"
  aria-label={label}
>
  <NumberFlow
    aria-hidden="true"
    value={parts ? hour : Number(fact.value)}
    suffix={parts ? undefined : fact.suffix}
    locales="en-US"
    format={{ useGrouping: !parts }}
    {transformTiming}
    respectMotionPreference={true}
  />
  {#if parts}<span class="mx-[0.02em] colon" aria-hidden="true">:</span
    ><NumberFlow
      aria-hidden="true"
      value={minute}
      locales="en-US"
      format={{ minimumIntegerDigits: 2, useGrouping: false }}
      {transformTiming}
      respectMotionPreference={true}
    /><span
      class="text-[0.25em] tracking-[0.015em] ml-[0.45em] text-muted period"
      aria-hidden="true">{period}</span
    >{/if}
</span>

<style>
  .value {
    --number-flow-mask-height: 0.08em;
  }
</style>
