<script lang="ts">
  import {
    TreemapChart,
    type TreemapChartOptions,
  } from "@carbon/charts-svelte";
  import "@carbon/charts-svelte/styles.css";
  import type { SubjectCourseStat } from "$lib/types/subject-stats.ts";
  import { CourseUtils } from "$lib/types/course.ts";
  import { getCarbonTheme } from "$lib/theme.ts";
  import { mode } from "mode-watcher";

  // beyond this the smallest tiles are unlabeled slivers
  const MAX_COURSES = 40;

  interface Props {
    courses: SubjectCourseStat[];
  }

  let { courses }: Props = $props();

  function levelLabel(courseNumber: number): string {
    return `${Math.floor(courseNumber / 100) * 100}-level`;
  }

  let data = $derived.by(() => {
    const largest = [...courses]
      .filter((course) => course.grades_given > 0)
      .sort((a, b) => b.grades_given - a.grades_given)
      .slice(0, MAX_COURSES);

    const byLevel = new Map<string, { name: string; value: number }[]>();
    for (const course of largest) {
      const label = levelLabel(course.course_reference.course_number);
      const children = byLevel.get(label) ?? [];
      children.push({
        name: CourseUtils.courseReferenceToString(course.course_reference),
        value: course.grades_given,
      });
      byLevel.set(label, children);
    }

    return [...byLevel.entries()]
      .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))
      .map(([name, children]) => ({ name, children }));
  });

  let options: TreemapChartOptions = $derived({
    title: "Largest Courses by Grades Given",
    height: "500px",
    theme: getCarbonTheme(mode.current),
  });
</script>

<TreemapChart {data} {options} />
