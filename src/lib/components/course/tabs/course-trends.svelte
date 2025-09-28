<script lang="ts">
  import ComboGradeDataStackedAreaChart from "$lib/components/charts/combo-grade-data-stacked-area-chart.svelte";
  import { Card, CardContent } from "$lib/components/ui/card/index.js";
  import type { Terms } from "$lib/types/terms.ts";
  import type { Course } from "$lib/types/course.ts";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    course: Course;
    terms: Terms;
  }

  let { course, terms }: Props = $props();
</script>

<Card>
  <CardContent class="pt-6">
    {#if course.cumulative_grade_data}
      <ComboGradeDataStackedAreaChart term_data={course.term_data} {terms} />
    {:else}
      <p class="text-center">{m["course.trends.noDataAvailable"]()}</p>
    {/if}
  </CardContent>
</Card>
