<script lang="ts">
  import {
    AreaChart,
    type AreaChartOptions,
    type ChartTabularData,
    ScaleTypes,
  } from "@carbon/charts-svelte";
  import "@carbon/charts-svelte/styles.css";
  import type { GradeData } from "$lib/types/madgrades.ts";
  import type { Terms } from "$lib/types/terms.ts";
  import { getCarbonTheme } from "$lib/theme.ts";
  import { mode } from "mode-watcher";

  interface Props {
    gradesByTerm: {
      [key: string]: GradeData;
    };
    terms: Terms;
  }

  let { gradesByTerm, terms }: Props = $props();

  let data: ChartTabularData = $derived(
    Object.entries(gradesByTerm)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([termCode, gradeData]) => ({
        group: "Enrollment",
        term: terms[termCode] ?? termCode,
        value: gradeData.total,
      })),
  );

  let options: AreaChartOptions = $derived({
    title: "Enrollment Over Terms",
    axes: {
      left: {
        title: "Students Graded",
        scaleType: ScaleTypes.LINEAR,
        mapsTo: "value",
      },
      bottom: {
        title: "Term",
        scaleType: ScaleTypes.LABELS,
        mapsTo: "term",
      },
    },
    curve: "curveMonotoneX",
    legend: {
      enabled: false,
    },
    height: "400px",
    theme: getCarbonTheme(mode.current),
  });
</script>

<AreaChart {data} {options} />
