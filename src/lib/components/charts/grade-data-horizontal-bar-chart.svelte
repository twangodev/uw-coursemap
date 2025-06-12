<script lang="ts">
  import { getTotalOtherGrades, type GradeData } from "$lib/types/madgrades.ts";
  import {
    type BarChartOptions,
    BarChartSimple,
    type ChartTabularData,
    ScaleTypes,
  } from "@carbon/charts-svelte";
  import "@carbon/charts-svelte/styles.css";
  import { getCarbonTheme } from "$lib/theme.ts";
  import { mode } from "mode-watcher";
  import type { TermData } from "$lib/types/course.ts";
  import { Button } from "$lib/components/ui/button/index.js";

  interface Props {
    cumulative: GradeData;
    termData: {
      [key: string]: TermData;
    };
    term?: string | null;
  }

  let { cumulative, termData, term = null }: Props = $props();

  // Toggle state for percentage/count view
  let showPercentages = $state(true);
  
  let gradeData = $derived(
    term ? (termData[term].grade_data ?? cumulative) : cumulative,
  );

  // Calculate raw data
  let rawData = $derived([
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
  ]);

  // Dynamic data processing for percentage/count toggle
  let data: ChartTabularData = $derived(
    showPercentages && gradeData.total > 0
      ? rawData.map(item => ({
          ...item,
          value: Number(((item.value / gradeData.total) * 100).toFixed(1))
        })).reverse()
      : rawData.slice().reverse()
  );

  // Enhanced chart options with dynamic configuration
  let options: BarChartOptions = $derived({
    title: "Grade Distribution",
    axes: {
      left: {
        mapsTo: "group",
        scaleType: ScaleTypes.LABELS,
      },
      bottom: {
        mapsTo: "value",
        title: showPercentages ? "Percentage" : "Count"
      },
    },
    legend: {
      order: ["A", "AB", "B", "BC", "C", "D", "F"],
    },
    toolbar: {
      enabled: false,
    },
    // Disable animations to prevent numbers sliding when switching views
    animations: false,
    // Custom tooltip implementation
    tooltip: {
      valueFormatter: (value: number) => showPercentages ? `${value}%` : value.toString(),
      customHTML: (data: any) => {
        const dataPoint = data[0];
        const displayValue = showPercentages 
          ? `${dataPoint.value}%` 
          : `${dataPoint.value}/${gradeData.total}`;
        return `
          <div class="bg-background border border-border rounded p-2 shadow-md">
            <div class="text-sm">
              <span class="font-medium">${dataPoint.group}</span>: ${displayValue}
            </div>
          </div>
        `;
      }
    },
    theme: getCarbonTheme(mode.current),
  });

  // Button click handlers
  function setPercentageView() {
    showPercentages = true;
  }

  function setCountView() {
    showPercentages = false;
  }
</script>

<div class="h-full relative">
  <!-- Count/Percentage Toggle Buttons -->
  <div class="absolute top-2 right-2 z-10 flex rounded-md border border-border bg-background/95 backdrop-blur-sm shadow-sm">
    <Button
      onclick={setCountView}
      variant={!showPercentages ? "default" : "ghost"}
      size="sm"
      class="rounded-r-none border-r border-border/50 text-xs px-3 py-1 h-7"
    >
      Count
    </Button>
    <Button
      onclick={setPercentageView}
      variant={showPercentages ? "default" : "ghost"}
      size="sm"
      class="rounded-l-none text-xs px-3 py-1 h-7"
    >
      Percentage
    </Button>
  </div>
  
  <BarChartSimple {data} {options} />
</div>
