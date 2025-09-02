<script lang="ts">
  import { onMount } from "svelte";
  import { env } from "$env/dynamic/public";
  import type { QuickStatistics } from "$lib/types/misc.ts";
  import { Marquee } from "$lib/components/ui/marquee/index.js";
  import { inView } from "$lib/actions/in-view";

  let quickStatistics = $state<QuickStatistics | undefined>(undefined);

  const PUBLIC_API_URL = env.PUBLIC_API_URL;

  let stats = $derived([
    {
      name: "Total Courses",
      value: formatNumber(quickStatistics?.total_courses || 0),
    },
    {
      name: "Grades Given",
      value: formatNumber(quickStatistics?.total_grades_given?.total || 0),
    },
    {
      name: "Total Instructors",
      value: formatNumber(quickStatistics?.total_instructors || 0),
    },
    {
      name: "Total Comments",
      value: formatNumber(quickStatistics?.total_ratings || 0),
    },
    {
      name: "Total Requisites",
      value: formatNumber(quickStatistics?.total_detected_requisites || "N/A"),
    },
  ]);

  let shuffledStats = $derived.by(() => {
    return stats.sort(() => Math.random() - 0.5);
  });

  function formatNumber(value: number | string): string {
    if (typeof value === "string") {
      return value;
    }

    if (value >= 1_000_000) {
      const truncatedMillions = Math.floor((value / 1_000_000) * 10) / 10;
      return `${truncatedMillions.toFixed(1)}M+`;
    }
    if (value >= 1_000) {
      const truncatedThousands = Math.floor((value / 1_000) * 10) / 10;
      return `${truncatedThousands.toFixed(1)}K+`;
    }
    return value.toString();
  }

  onMount(async () => {
    const response = await fetch(`${PUBLIC_API_URL}/quick_statistics.json`);
    if (!response.ok) {
      console.error("Failed to fetch quick statistics:", response.statusText);
      return;
    }

    quickStatistics = await response.json();
  });
</script>

<div use:inView={{ threshold: 0.4 }} class="mx-auto w-full max-w-6xl px-3 py-20">
  <span
    class="z-10 block w-fit rounded-lg border border-rose-200/20 bg-rose-50/50 px-3 py-1.5 leading-4 font-semibold tracking-tighter uppercase sm:text-sm dark:border-rose-800/30 dark:bg-rose-900/20 opacity-0 animate-fade-up [animation-fill-mode:forwards] [&.in-view]:opacity-100"
  >
    <span
      class="bg-gradient-to-b from-rose-500 to-rose-600 bg-clip-text text-transparent dark:from-rose-200 dark:to-rose-400"
      >Aggregated Statistics</span
    >
  </span>
  <h2
    id="features-title"
    class="mt-2 inline-block bg-gradient-to-br from-gray-900 to-gray-800 bg-clip-text py-2 text-4xl font-bold tracking-tighter text-transparent sm:text-5xl dark:from-gray-50 dark:to-gray-300 opacity-0 animate-fade-up [animation-delay:100ms] [animation-fill-mode:forwards] [&.in-view]:opacity-100"
  >
    Dynamic Insights from Multiple Sources
  </h2>
  <p class="mt-6 max-w-3xl text-lg leading-7 text-gray-600 dark:text-gray-400 opacity-0 animate-fade-up [animation-delay:200ms] [animation-fill-mode:forwards] [&.in-view]:opacity-100">
    UW Course Map brings everything into one place—pulling data from Rate My
    Professor, Madgrades, UW-Madison's Course &amp; Enroll, Course Guide, and
    more—so you can view key metrics (GPA, prerequisite paths, average ratings,
    distributions, etc.) all in a single dashboard.
  </p>
  <dl class="mt-12 border-y border-gray-200 py-14 dark:border-gray-800">
    <Marquee pauseOnHover class="[--duration:30s]">
      <div class="flex">
        {#each shuffledStats as stat}
          <div
            class="w-48 border-l-2 border-rose-100 text-center md:w-72 lg:border-gray-200 dark:border-rose-900 lg:dark:border-gray-800"
          >
            <dd
              class="inline-block bg-gradient-to-t from-rose-900 to-rose-600 bg-clip-text text-5xl font-bold tracking-tight text-transparent lg:text-6xl dark:from-rose-700 dark:to-rose-400"
            >
              {stat.value}
            </dd>
            <dt class="mt-1 text-gray-600 dark:text-gray-400">
              {stat.name}
            </dt>
          </div>
        {/each}
      </div>
    </Marquee>
  </dl>
</div>
