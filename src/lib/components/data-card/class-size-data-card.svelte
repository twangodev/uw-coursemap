<script lang="ts">
  import { GenericDataCard } from "$lib/components/data-card/index.js";
  import { Users } from "@lucide/svelte";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    termClassSize: number | null;
    cumulativeAverageClassSize: number | null;
  }

  let { termClassSize, cumulativeAverageClassSize }: Props = $props();
</script>

<GenericDataCard
  title={m["course.dataCards.classSize"]()}
  icon={Users}
  value={termClassSize}
  reference={cumulativeAverageClassSize}
  comparisonKeyword={m["course.dataCards.historical"]()}
/>
