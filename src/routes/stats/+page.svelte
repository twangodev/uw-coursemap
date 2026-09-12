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

<div class="school-stats">
  <header class="intro">
    <div>
      <h1>UW–Madison statistics.</h1>
    </div>
    <TermPicker {terms} value={term} label="Statistics term" onChange={changeTerm} />
  </header>
  <div class="bento-grid">
    <StatsCard title="Campus activity" span={8}>
      {#snippet preview()}
        <SchoolBuildingMap buildings={current.schedule.buildings} preview />
        {#if !current.schedule.meetings}<span class="preview-label"
            >No building schedule for {termName(term)}</span
          >{/if}
      {/snippet}
      {#if current.schedule.meetings}
        <SchoolBuildingMap buildings={current.schedule.buildings} />
        <details class="disclosure">
          <summary>Where the teaching happens</summary>
          <div class="building-list">
            {#each current.schedule.buildings.slice(0, 10) as building}<div>
                <span>{building.name}</span><span
                  >{building.knownMeetings
                    ? building.enrolledVisits.toLocaleString()
                    : "—"}
                  <small>enrollment visits</small></span
                >
              </div>{/each}
          </div>
        </details>
      {:else}<p class="empty">
          We don’t have a building schedule for {termName(term)} in this dataset.
        </p>{/if}
    </StatsCard>
    <StatsCard compact title="Courses" span={4}>
      {#snippet preview()}
        <strong class="preview-number"
          ><AnimatedNumber
            value={current.courses || current.recordedCourses || null}
          /></strong
        >
        <span class="preview-label"
          >{current.courses
            ? "courses offered"
            : "courses with recorded grades"}</span
        >
        <span class="preview-term">{termName(term)}</span>
      {/snippet}
      <div class="headlines">
        <div>
          <strong
            ><AnimatedNumber
              value={current.courses || current.recordedCourses || null}
            /></strong
          ><span
            >{current.courses
              ? "courses offered"
              : "courses with recorded grades"}</span
          >
        </div>
        <div>
          <strong
            ><AnimatedNumber
              value={(current.courses
                ? current.instructors
                : current.recordedInstructors) || null}
            /></strong
          ><span>recorded instructors</span>
        </div>
        <div>
          <strong
            ><AnimatedNumber
              value={current.sections || current.gradedSections || null}
            /></strong
          ><span
            >{current.sections
              ? "recorded class sections"
              : "sections with recorded grades"}</span
          >
        </div>
      </div>

      <a class="browse-link" href="/search"
        >Browse courses <ArrowUpRight size={14} /></a
      >
    </StatsCard>
    <StatsCard title="Busiest hour" span={4}>
      {#snippet preview()}
        {#if peak}
          <strong class="preview-number time"
            >{weekdays[peak.day]}, {timeLabel(peak.hour)}.</strong
          >
          <div
            class="week-preview"
            style={`--hours:${hours.length}`}
            aria-hidden="true"
          >
            {#each weekdays as day, d}{#each hours as hour}{@const count =
                  current.schedule.cells.find(
                    (c) => c.day === d && c.hour === hour,
                  )?.meetings ?? 0}<span
                  style:opacity={count
                    ? 0.12 + Math.sqrt(count / peak.meetings) * 0.88
                    : 0.04}
                ></span>{/each}{/each}
          </div>
        {:else}<span class="preview-number">—</span><span class="preview-label"
            >No schedule recorded</span
          >{/if}
      {/snippet}
      {#if current.schedule.meetings}<div class="clock-detail">
          <div class="heat-panel">
            <p class="observation">
              <strong>{weekdays[peak.day]}, {timeLabel(peak.hour)}.</strong>
              <span class="observation-label">Campus at its busiest.</span>
            </p>
            <div
              class="heatmap"
              style={`--hours:${hours.length}`}
              role="group"
              aria-label="Scheduled meetings by weekday and hour"
            >
              <span></span>{#each hours as hour}<span class="hour"
                  >{hour % 3 === 1 ? timeLabel(hour) : ""}</span
                >{/each}
              {#each weekdays as day, d}<span class="day">{day}</span
                >{#each hours as hour}{@const count =
                    current.schedule.cells.find(
                      (c) => c.day === d && c.hour === hour,
                    )?.meetings ?? 0}<button
                    class="cell"
                    style={`--intensity:${count ? 0.12 + Math.sqrt(count / peak.meetings) * 0.8 : 0.03}`}
                    aria-label={`${day} ${timeLabel(hour)}: ${count.toLocaleString()} scheduled meetings`}
                    onpointerenter={() => (activeCell = { day: d, hour })}
                    onfocus={() => (activeCell = { day: d, hour })}
                    onclick={() => (activeCell = { day: d, hour })}
                  ></button>{/each}{/each}
            </div>
            <p class="heat-detail" aria-live="polite">
              {#if activeCell}{weekdays[activeCell.day]} at {timeLabel(
                  activeCell.hour,
                )} · {(cellDetail?.meetings ?? 0).toLocaleString()} meetings across
                the recorded term{:else}Hover to explore.{/if}
            </p>
          </div>
        </div>{:else}<p class="empty">
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

  <details class="methodology">
    <summary>About these numbers</summary>
    <p>
      Derived from the published dataset, scanned {data.status.observed_at.slice(
        0,
        10,
      )}. Coverage varies by term. Missing records are not treated as zero.
    </p>
    <p>
      Meetings count once per occupied hour, including partial hours. The map
      counts recorded enrollment for each scheduled meeting: the same enrollment
      is counted again when a class meets again. These are enrollment visits,
      not unique students or actual attendance.
    </p>
    <p>
      Course identities and section IDs are deduplicated across listings.
      Lecture totals exclude labs and discussions; building enrollment excludes
      meetings with unknown enrollment. Grades use the import’s reconciled
      course/term totals, weighted by letter-grade counts, without adding
      section totals again. Trends reflect the courses and grades recorded each
      term, not changes in the same students.
    </p>
    <p>
      All observations are calculated from the data, not generated by an LLM.
    </p>
  </details>
</div>

<style>
  .school-stats {
    padding: 30px 0 10px;
  }
  .intro {
    display: flex;
    justify-content: space-between;
    gap: 30px;
    align-items: flex-start;
  }
  .headlines {
    display: flex;
    gap: clamp(30px, 8vw, 120px);
    padding: 34px 0 10px;
  }
  .headlines > div {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }
  .headlines strong {
    font-size: clamp(28px, 4vw, 48px);
    font-weight: 500;
    letter-spacing: -0.04em;
  }
  .headlines span {
    font-size: 13px;
    color: var(--muted);
  }
  .observation {
    font-size: 42px;
    line-height: 1.1;
    letter-spacing: -0.02em;
    max-width: 430px;
    margin: 0 0 26px;
  }
  .observation strong {
    font-weight: 500;
    color: var(--text);
  }
  .observation-label {
    display: block;
    font-size: 13px;
    color: var(--muted);
    margin-top: 10px;
    letter-spacing: 0;
  }
  .heatmap {
    display: grid;
    grid-template-columns: 30px repeat(var(--hours), minmax(0, 1fr));
    gap: 4px;
    align-items: center;
  }
  .hour {
    font-size: 9px;
    color: var(--muted);
    height: 22px;
    white-space: nowrap;
  }
  .day {
    font-size: 11px;
    color: var(--muted);
  }
  .cell {
    padding: 0;
    width: 100%;
    min-width: 0;
    aspect-ratio: 1;
    border: 0;
    border-radius: 3px;
    cursor: pointer;
    background: color-mix(
      in srgb,
      var(--accent) calc(var(--intensity) * 100%),
      var(--surface)
    );
    transition: transform 150ms;
  }
  .cell:hover,
  .cell:focus-visible {
    outline: 2px solid var(--text);
    outline-offset: 1px;
    transform: scale(1.1);
  }
  .heat-detail {
    font-size: 12px;
    color: var(--muted);
    min-height: 36px;
    margin-top: 18px;
  }
  .disclosure {
    margin-top: 25px;
    font-size: 13px;
  }
.building-list{
    margin-top: 16px;
    max-height: 320px;
    overflow: auto;
  }
.building-list > div{
    display: flex;
    justify-content: space-between;
    gap: 20px;
    padding: 8px 0;
  }
  .methodology {
    margin: 65px 0 35px;
    padding-top: 25px;
    border-top: 1px solid var(--border);
    font-size: 13px;
    line-height: 1.7;
  }
  .methodology p {
    max-width: 780px;
    color: var(--muted);
  }
  .empty {
    padding: 30px 0;
    color: var(--muted);
    line-height: 1.7;
    max-width: 580px;
  }
  .bento-grid {
    display: grid;
    grid-template-columns: repeat(12, minmax(0, 1fr));
    gap: 20px;
    margin-top: 38px;
    align-items: start;
  }
  .preview-number {
    display: block;
    font-size: clamp(40px, 4.5vw, 68px);
    letter-spacing: -0.06em;
    font-weight: 450;
    line-height: 1.05;
  }
  .preview-number.time {
    font-size: clamp(28px, 3vw, 44px);
  }
  .preview-label,
  .preview-term {
    display: block;
    color: var(--muted);
    font-size: 12px;
    margin-top: 12px;
  }
  .preview-term {
    margin-top: auto;
  }
  .week-preview {
    display: grid;
    grid-template-columns: repeat(var(--hours), 1fr);
    gap: 3px;
    margin-top: 24px;
  }
  .week-preview span {
    background: var(--accent);
    aspect-ratio: 1.4;
    border-radius: 2px;
  }
  .clock-detail {
    max-width: 760px;
  }
  .browse-link {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-top: 24px;
    font-size: 14px;
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
    .headlines span {
      font-size: 11px;
    }
    .school-stats {
      padding-top: 15px;
    }}
  @media (prefers-reduced-motion: reduce) {
    .cell {
      transition: none;
    }}
</style>
