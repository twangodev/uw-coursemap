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

  function levelLabel(level: number): string {
    return level === 0 ? "Below 100" : `${level}-level`;
  }

  let data = $derived.by(() => {
    const largest = courses
      .filter((course) => course.grades_given > 0)
      .slice(0, MAX_COURSES);

    const byLevel = new Map<number, { name: string; value: number }[]>();
    for (const course of largest) {
      const level =
        Math.floor(course.course_reference.course_number / 100) * 100;
      const children = byLevel.get(level) ?? [];
      children.push({
        name: CourseUtils.courseReferenceToString(course.course_reference),
        value: course.grades_given,
      });
      byLevel.set(level, children);
    }

    return [...byLevel.entries()]
      .sort(([a], [b]) => a - b)
      .map(([level, children]) => ({ name: levelLabel(level), children }));
  });

  let options: TreemapChartOptions = $derived({
    title: "Largest Courses by Grades Given",
    height: "500px",
    theme: getCarbonTheme(mode.current),
  });
</script>

<TreemapChart {data} {options} />
