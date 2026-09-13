<script lang="ts">
  import { BarChart, LineChart, AreaChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX } from "d3-shape";
  import { goto } from "$app/navigation";
  import { ArrowUpRight } from "@lucide/svelte";
  import SchoolGrades from "$lib/components/SchoolGrades.svelte";
  import SchoolClassrooms from "$lib/components/SchoolClassrooms.svelte";
  import TermPicker from "$lib/components/TermPicker.svelte";
  import StatsCard from "$lib/components/StatsCard.svelte";
  import Disclosure from "$lib/components/Disclosure.svelte";
  import Metric from "$lib/components/Metric.svelte";
  import AnimatedNumber from "$lib/components/AnimatedNumber.svelte";
  import SchoolAcademics from "$lib/components/SchoolAcademics.svelte";
  import SchoolBuildingMap from "$lib/components/SchoolBuildingMap.svelte";
  import { termName, courseUrl, courseTitle } from "$lib/format";
  import { type SchoolStats } from "$lib/school-stats";
  let { data } = $props();
  let stats: SchoolStats = $derived(data.schoolStats);
  let term = $derived(stats.selectedTerm);
  let terms = $derived(Object.keys(stats.terms).sort().reverse());
  let current = $derived(stats.terms[term]);
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const timeLabel = (h: number) => `${h % 12 || 12}${h < 12 ? "am" : "pm"}`;
  let peak = $derived(
    [...current.schedule.cells].sort(
      (a, b) => b.meetings - a.meetings || a.day - b.day || a.hour - b.hour,
    )[0],
  );
  let hours = $derived(
    Array.from({ length: 24 }, (_, i) => i).filter(
      (h) =>
        (h >= 7 && h <= 21) || current.schedule.cells.some((c) => c.hour === h),
    ),
  );
  let activeCell = $state<{ day: number; hour: number } | null>(null);
  let cellDetail = $derived(
    activeCell
      ? current.schedule.cells.find(
          (c) => c.day === activeCell!.day && c.hour === activeCell!.hour,
        )
      : null,
  );
  function changeTerm(value: string) {
    activeCell = null;
    goto(`/stats?term=${value}`, { noScroll: true, keepFocus: true });
  }
</script>

<div class="pt-7.5 pb-2.5 school-stats px-0">
  <header class="flex justify-between gap-7.5 items-start intro">
    <div>
      <h1>UW–Madison statistics.</h1>
    </div>
    <TermPicker
      {terms}
      value={term}
      label="Statistics term"
      onChange={changeTerm}
    />
  </header>
  <div class="grid grid-cols-12 gap-5 mt-9.5 items-start bento-grid">
    <StatsCard title="Campus activity" span={8}>
      {#snippet preview()}
        <SchoolBuildingMap buildings={current.schedule.buildings} preview />
        {#if !current.schedule.meetings}<span
            class="block text-muted text-[12px] mt-3 preview-label"
            >No building schedule for {termName(term)}</span
          >{/if}
      {/snippet}
      {#if current.schedule.meetings}
        <SchoolBuildingMap buildings={current.schedule.buildings} />
        <details class="mt-[25px] text-[13px] disclosure">
          <summary>Where the teaching happens</summary>
          <div class="mt-4 max-h-80 overflow-auto building-list">
            {#each current.schedule.buildings.slice(0, 10) as building}<div
                class="flex justify-between gap-5 py-2 px-0"
              >
                <span>{building.name}</span><span
                  >{building.knownMeetings
                    ? building.enrolledVisits.toLocaleString()
                    : "—"}
                  <small>enrollment visits</small></span
                >
              </div>{/each}
          </div>
        </details>
      {:else}<p class="text-muted leading-[1.7] max-w-145 empty py-7.5 px-0">
          We don’t have a building schedule for {termName(term)} in this dataset.
        </p>{/if}
    </StatsCard>
    <StatsCard compact title="Courses" span={4}>
      {#snippet preview()}
        <strong
          class="block text-[clamp(40px,_4.5vw,_68px)] tracking-[-0.06em] font-[450] leading-[1.05] preview-number"
          ><AnimatedNumber
            value={current.courses || current.recordedCourses || null}
          /></strong
        >
        <span class="block text-muted text-[12px] mt-3 preview-label"
          >{current.courses
            ? "courses offered"
            : "courses with recorded grades"}</span
        >
        <span class="block text-muted text-[12px] mt-auto preview-term"
          >{termName(term)}</span
        >
      {/snippet}
      <div
        class="flex gap-[clamp(30px,_8vw,_120px)] pt-8.5 pb-2.5 headlines px-0"
      >
        <Metric
          variant="headline"
          value={current.courses || current.recordedCourses || null}
          label={current.courses
            ? "courses offered"
            : "courses with recorded grades"}
        />
        <Metric
          variant="headline"
          value={(current.courses
            ? current.instructors
            : current.recordedInstructors) || null}
          label="recorded instructors"
        />
        <Metric
          variant="headline"
          value={current.sections || current.gradedSections || null}
          label={current.sections
            ? "recorded class sections"
            : "sections with recorded grades"}
        />
      </div>

      <a
        class="inline-flex items-center gap-2.5 mt-6 text-[14px] browse-link"
        href="/search">Browse courses <ArrowUpRight size={14} /></a
      >
    </StatsCard>
    <StatsCard title="Busiest hour" span={4}>
      {#snippet preview()}
        {#if peak}
          <strong
            class="block text-[clamp(28px,_3vw,_44px)] tracking-[-0.06em] font-[450] leading-[1.05] preview-number time"
            >{weekdays[peak.day]}, {timeLabel(peak.hour)}.</strong
          >
          <div
            class="grid grid-cols-[repeat(var(--hours),_1fr)] gap-[3px] mt-6 week-preview"
            style={`--hours:${hours.length}`}
            aria-hidden="true"
          >
            {#each weekdays as day, d}{#each hours as hour}{@const count =
                  current.schedule.cells.find(
                    (c) => c.day === d && c.hour === hour,
                  )?.meetings ?? 0}<span
                  class="bg-accent [aspect-ratio:1.4] rounded-[2px]"
                  style:opacity={count
                    ? 0.12 + Math.sqrt(count / peak.meetings) * 0.88
                    : 0.04}
                ></span>{/each}{/each}
          </div>
        {:else}<span
            class="block text-[clamp(40px,_4.5vw,_68px)] tracking-[-0.06em] font-[450] leading-[1.05] preview-number"
            >—</span
          ><span class="block text-muted text-[12px] mt-3 preview-label"
            >No schedule recorded</span
          >{/if}
      {/snippet}
      {#if current.schedule.meetings}<div class="max-w-190 clock-detail">
          <div class="heat-panel">
            <p
              class="text-[42px] leading-[1.1] tracking-[-0.02em] max-w-107.5 mt-0 mb-6.5 observation mx-0"
            >
              <strong class="font-medium text-foreground"
                >{weekdays[peak.day]}, {timeLabel(peak.hour)}.</strong
              >
              <span
                class="block text-[13px] text-muted mt-2.5 tracking-[0] observation-label"
                >Campus at its busiest.</span
              >
            </p>
            <div
              class="grid grid-cols-[30px_repeat(var(--hours),_minmax(0,_1fr))] gap-1 items-center heatmap"
              style={`--hours:${hours.length}`}
              role="group"
              aria-label="Scheduled meetings by weekday and hour"
            >
              <span></span>{#each hours as hour}<span
                  class="text-[9px] text-muted h-5.5 whitespace-nowrap hour"
                  >{hour % 3 === 1 ? timeLabel(hour) : ""}</span
                >{/each}
              {#each weekdays as day, d}<span class="text-[11px] text-muted day"
                  >{day}</span
                >{#each hours as hour}{@const count =
                    current.schedule.cells.find(
                      (c) => c.day === d && c.hour === hour,
                    )?.meetings ?? 0}<button
                    class="p-0 w-full min-w-0 aspect-square border-0 rounded-[3px] cursor-pointer bg-[color-mix(_in_srgb,_var(--accent)_calc(var(--intensity)_*_100%),_var(--surface)_)] cell"
                    style={`--intensity:${count ? 0.12 + Math.sqrt(count / peak.meetings) * 0.8 : 0.03}`}
                    aria-label={`${day} ${timeLabel(hour)}: ${count.toLocaleString()} scheduled meetings`}
                    onpointerenter={() => (activeCell = { day: d, hour })}
                    onfocus={() => (activeCell = { day: d, hour })}
                    onclick={() => (activeCell = { day: d, hour })}
                  ></button>{/each}{/each}
            </div>
            <p
              class="text-[12px] text-muted min-h-9 mt-4.5 heat-detail"
              aria-live="polite"
            >
              {#if activeCell}{weekdays[activeCell.day]} at {timeLabel(
                  activeCell.hour,
                )} · {(cellDetail?.meetings ?? 0).toLocaleString()} meetings across
                the recorded term{:else}Hover to explore.{/if}
            </p>
          </div>
        </div>{:else}<p
          class="text-muted leading-[1.7] max-w-145 empty py-7.5 px-0"
        >
          No meeting schedule recorded for {termName(term)}.
        </p>{/if}
    </StatsCard>
    <SchoolClassrooms {current} />
    <SchoolGrades {stats} {term} />
    {#if stats.academics}{#key term}<SchoolAcademics
          academics={stats.academics}
          selectedTerm={term}
        />{/key}{/if}
  </div>

  <details
    class="mt-[65px] mb-[35px] pt-[25px] border-t border-t-border text-[13px] leading-[1.7] methodology mx-0"
  >
    <summary>About these numbers</summary>
    <p class="max-w-195 text-muted">
      Derived from the published dataset, scanned {data.status.observed_at.slice(
        0,
        10,
      )}. Coverage varies by term. Missing records are not treated as zero.
    </p>
    <p class="max-w-195 text-muted">
      Meetings count once per occupied hour, including partial hours. The map
      counts recorded enrollment for each scheduled meeting: the same enrollment
      is counted again when a class meets again. These are enrollment visits,
      not unique students or actual attendance.
    </p>
    <p class="max-w-195 text-muted">
      Course identities and section IDs are deduplicated across listings.
      Lecture totals exclude labs and discussions; building enrollment excludes
      meetings with unknown enrollment. Grades use the import’s reconciled
      course/term totals, weighted by letter-grade counts, without adding
      section totals again. Trends reflect the courses and grades recorded each
      term, not changes in the same students.
    </p>
    <p class="max-w-195 text-muted">
      All observations are calculated from the data, not generated by an LLM.
    </p>
  </details>
</div>

<style>
  .cell {
    transition: transform 150ms;
  }
  .cell:hover,
  .cell:focus-visible {
    outline: 2px solid var(--text);
    outline-offset: 1px;
    transform: scale(1.1);
  }
  @media (max-width: 760px) {
    .intro {
      flex-direction: column;
      gap: 15px;
    }
    .headlines {
      gap: 25px;
      justify-content: space-between;
    }
    .school-stats {
      padding-top: 15px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .cell {
      transition: none;
    }
  }
</style>
