<script lang="ts">
  import { getTotalOtherGrades, type GradeData } from "$lib/types/madgrades.ts";
  import {
    type BarChartOptions,
    BarChartSimple,
    type ChartTabularData,
    MeterChart, type MeterChartOptions,
    ScaleTypes,
  } from "@carbon/charts-svelte";
  import "@carbon/charts-svelte/styles.css";
  import { getCarbonTheme } from "$lib/theme.ts";
  import { mode } from "mode-watcher";
  import type { TermData } from "$lib/types/course.ts";
  import type {Terms} from "$lib/types/terms.ts";
  import {onMount} from "svelte";

  interface Props {
    cumulative: GradeData;
    termData: {
      [key: string]: TermData;
    };
    term?: string | null;
    terms: Terms
  }

  let { cumulative, termData, term, terms }: Props = $props();

  let hasAvailableTermData = $derived.by(() => {
    if (!term || !termData) return false;
    return Object.keys(termData).length > 0 && termData[term] != null;
  })

  let currentTermName = $derived(
    hasAvailableTermData ? terms[term!] : "Cumulative",
  );

  let gradeData: GradeData = $derived(
    hasAvailableTermData ? termData[term!].grade_data ?? cumulative : cumulative,
  );

  let data: ChartTabularData = $derived(
    [
      {
        group: "A",
        value: gradeData.a,
      },
      {
        group: "AB",
        value: gradeData.ab,
      },
      {
        group: "B",
        value: gradeData.b,
      },
      {
        group: "BC",
        value: gradeData.bc,
      },
      {
        group: "C",
        value: gradeData.c,
      },
      {
        group: "D",
        value: gradeData.d,
      },
      {
        group: "F",
        value: gradeData.f,
      },
      {
        group: "Other",
        value: getTotalOtherGrades(gradeData),
      },
    ].reverse(),
  );

  const colorScale = {
    A:   "#2ECC71",
    AB:  "#27AE60",
    B:   "#F1C40F",
    BC:  "#F39C12",
    C:   "#E67E22",
    D:   "#E74C3C",
    F:   "#C0392B",
    Other: "#6F6F6F",
  }

  let options: BarChartOptions = $derived({
    title: "Grade Distribution",
    axes: {
      left: {
        mapsTo: "group",
        scaleType: ScaleTypes.LABELS,
      },
      bottom: {
        mapsTo: "value",
      },
    },
    legend: {
      order: ["A", "AB", "B", "BC", "C", "D", "F"],
    },
    toolbar: {
      enabled: false,
    },
    theme: getCarbonTheme(mode.current),
    color: {
     scale: colorScale
    }
  });

  let meterData = $derived(data.toReversed())

  let meterOptions : MeterChartOptions = $derived({
    height: '30px',
    meter: {
      proportional: {
        total: gradeData.total,
        totalFormatter: (value: number) => ``,
      }
    },
    toolbar: {
      enabled: false,
    },
    theme: getCarbonTheme(mode.current),
    legend: {
      enabled: false,
    },
    color: {
      scale: colorScale
    },
    tooltip: {
      valueFormatter: (value: number) => `${(value * 100 / gradeData.total).toFixed(2)}%`
    }
  })


</script>

<div class="h-full">
  <BarChartSimple {data} {options} />
  <MeterChart data={meterData} options={meterOptions} />
  <p class="text-xs text-muted-foreground text-center mt-4">
    {currentTermName} Grade Distribution
  </p>
</div>
