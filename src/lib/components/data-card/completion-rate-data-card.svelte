<script lang="ts">
  import { GenericDataCard } from "$lib/components/data-card/index.js";
  import { CircleCheckBig } from "@lucide/svelte";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    termCompletionRate: number | null;
    cumulativeCompletionRate: number | null;
  }

  let { termCompletionRate, cumulativeCompletionRate }: Props = $props();
</script>

<GenericDataCard
  title={m["course.dataCards.completionRate"]()}
  icon={CircleCheckBig}
  value={termCompletionRate}
  suffix="%"
  reference={cumulativeCompletionRate}
  comparisonKeyword={m["course.dataCards.historical"]()}
/>
