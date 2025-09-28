<script lang="ts">
  import { GenericDataCard } from "$lib/components/data-card/index.js";
  import { BookPlus } from "@lucide/svelte";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    termGPA: number | null;
    cumulativeGPA: number | null;
  }

  let { termGPA, cumulativeGPA }: Props = $props();

  function calculateColorFromGPA(gpa: number | null) {
    if (gpa === null) {
      return "";
    }
    if (gpa >= 3.5) {
      return "text-green-600 dark:text-green-400";
    } else if (gpa >= 3.0) {
      return "text-amber-600 dark:text-yellow-400";
    } else if (gpa >= 2.5) {
      return "text-orange-600 dark:text-orange-400";
    } else {
      return "text-red-600 dark:text-red-400";
    }
  }
</script>

<GenericDataCard
  title={m["course.dataCards.gradePointAverage"]()}
  icon={BookPlus}
  class={calculateColorFromGPA(termGPA)}
  value={termGPA}
  reference={cumulativeGPA}
  comparisonKeyword={m["course.dataCards.historical"]()}
/>
