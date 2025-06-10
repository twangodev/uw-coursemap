<script lang="ts">
  import { GenericDataCard } from "$lib/components/data-card/index.js";
  import { Users } from "@lucide/svelte";

  interface Props {
    termClassSize: number | null;
    cumulativeAverageClassSize: number | null;
  }

  let { termClassSize, cumulativeAverageClassSize }: Props = $props();
</script>

<GenericDataCard
  title="Class Size"
  icon={Users}
  value={termClassSize}
  reference={cumulativeAverageClassSize}
  comparisonKeyword="Historical"
/>
