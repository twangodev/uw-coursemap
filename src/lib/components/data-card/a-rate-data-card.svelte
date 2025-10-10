<script lang="ts">
  import { GenericDataCard } from "$lib/components/data-card/index.js";
  import { BookA } from "@lucide/svelte";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    termARate: number | null;
    cumulativeARate: number | null;
  }

  let { termARate, cumulativeARate }: Props = $props();
</script>

<GenericDataCard
  title={m["course.dataCards.aRate"]()}
  icon={BookA}
  value={termARate}
  suffix="%"
  reference={cumulativeARate}
  comparisonKeyword={m["course.dataCards.historical"]()}
/>
