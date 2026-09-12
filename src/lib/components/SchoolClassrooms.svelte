<script lang="ts">
  import { BarChart } from "layerchart";
  import { ArrowUpRight } from "@lucide/svelte";
  import { courseUrl, courseTitle } from "$lib/format";
  import type { SchoolTerm } from "$lib/school-stats";
  import StatsCard from "./StatsCard.svelte";
  import Disclosure from "./Disclosure.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  let { current }: { current: SchoolTerm } = $props();
  let historicalClassroom = $derived(
    !current.knownLectures && current.gradedSections > 0,
  );
  let classroom = $derived(
    historicalClassroom
      ? {
          ...current,
          knownLectures: current.gradedSections,
          lectures: current.gradedSections,
          medianLecture: current.gradedMedian,
          sizes: current.gradedSizes,
        }
      : current,
  );
  let under50 = $derived(
    classroom.knownLectures
      ? (classroom.sizes.slice(0, 2).reduce((n, s) => n + s.count, 0) /
          classroom.knownLectures) *
          100
      : null,
  );
</script>

<StatsCard title="Class sizes" span={4}>
  {#snippet preview()}
    <strong class="preview-number"
      ><AnimatedNumber
        value={classroom.medianLecture}
        decimals={classroom.medianLecture && classroom.medianLecture % 1
          ? 1
          : 0}
      /></strong
    >
    <span class="preview-label"
      >{historicalClassroom
        ? "median outcomes per graded section"
        : "median lecture enrollment"}</span
    >
    <div class="preview-sizes">
      <div
        class="size-bubbles"
        role="img"
        aria-label="Section size distribution. Circle area represents the number of sections."
      >
        {#each classroom.sizes as size}
          <div>
            <svg viewBox="0 0 100 100" aria-hidden="true"
              ><circle
                cx="50"
                cy="50"
                r={Math.sqrt(
                  size.count /
                    Math.max(1, ...classroom.sizes.map((s) => s.count)),
                ) * 43}
                fill="var(--accent)"
                fill-opacity="0.7"
                ><title
                  >{size.label}: {size.count.toLocaleString()} sections</title
                ></circle
              ></svg
            ><span>{size.label}</span>
          </div>
        {/each}
      </div>
    </div>
    {#if under50 !== null}<span class="preview-math"
        >{under50.toFixed(1)}% of sections under 50</span
      >{/if}
  {/snippet}
  {#if classroom.knownLectures}
    <div class="story-grid classroom">
      <div>
        <p class="observation">
          <strong
            ><AnimatedNumber
              value={classroom.medianLecture}
              decimals={classroom.medianLecture! % 1 ? 1 : 0}
            />
          </strong>
          <span class="observation-label"
            >{historicalClassroom
              ? "median outcomes per graded section"
              : "median lecture enrollment"}</span
          >
        </p>
        <BarChart
          data={classroom.sizes}
          x="label"
          y="count"
          series={[
            {
              key: "count",
              label: historicalClassroom
                ? "Graded sections"
                : "Lecture sections",
              color: "var(--accent)",
            },
          ]}
          height={270}
          props={{
            bars: { strokeWidth: 0 },
            tooltip: { hideTotal: true },
          }}
        />

        <details class="disclosure">
          <summary>Section sizes & coverage</summary>
          <p class="coverage">
            {#if historicalClassroom}Based on {current.gradedSections.toLocaleString()}
              section grade records, including non-letter outcomes. These are recorded
              outcomes, not historical enrollment snapshots; section type is unavailable.{:else}Known
              enrollment for {current.knownLectures.toLocaleString()}
              of {current.lectures.toLocaleString()}
              lecture sections. Labs and discussions excluded.{/if}
          </p>

          <div class="grade-table">
            {#each classroom.sizes as size}<div>
                <span
                  >{size.label}
                  {historicalClassroom ? "outcomes" : "enrolled"}</span
                ><span>{size.count.toLocaleString()} sections</span>
              </div>{/each}
          </div>
        </details>
      </div>
      {#if !historicalClassroom}<Disclosure
          title="Largest classes"
          description="This term"
          ><div class="course-list">
            {#each current.largest as course, i}<a href={courseUrl(course.code)}
                ><span class="rank">{i + 1}</span><span class="course"
                  ><strong>{course.code}</strong><span
                    >{courseTitle(course.title)}</span
                  ></span
                ><span class="enrolled"
                  >{course.enrolled.toLocaleString()}<ArrowUpRight
                    size={14}
                  /></span
                ></a
              >{/each}
          </div></Disclosure
        >{/if}
    </div>
  {:else}<p class="empty">
      Lecture enrollment isn’t available for this term. Historical grades are
      shown below where available.
    </p>{/if}
</StatsCard>

<style>
  .story-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
    gap: clamp(28px, 5vw, 70px);
    align-items: start;
  }
  .story-grid > div {
    min-width: 0;
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
  .coverage {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
  }
  .course-list a {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px 0;
    border-bottom: 1px solid var(--border);
  }
  .rank {
    font-size: 12px;
    color: var(--muted);
  }
  .course {
    display: flex;
    flex: 1;
    min-width: 0;
    flex-direction: column;
    gap: 5px;
  }
  .course strong {
    font-size: 13px;
    font-weight: 500;
  }
  .course > span {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.4;
  }
  .enrolled {
    display: flex;
    gap: 10px;
    align-items: center;
    font-size: 14px;
  }
  .disclosure {
    margin-top: 25px;
    font-size: 13px;
  }

  .grade-table {
    margin-top: 16px;
    max-height: 320px;
    overflow: auto;
  }

  .grade-table > div {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    padding: 8px 0;
  }
  .empty {
    padding: 30px 0;
    color: var(--muted);
    line-height: 1.7;
    max-width: 580px;
  }
  .size-bubbles {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    align-items: end;
    gap: 10px;
    min-height: 180px;
    padding-bottom: 20px;
  }
  .size-bubbles svg {
    display: block;
    width: 100%;
  }
  .size-bubbles span {
    display: block;
    text-align: center;
    font-size: 11px;
    color: var(--muted);
    margin-top: 18px;
  }
  .preview-math {
    display: block;
    color: var(--muted);
    font-size: 11px;
    margin-top: 14px;
    font-variant-numeric: tabular-nums;
  }
  .preview-number {
    display: block;
    font-size: clamp(40px, 4.5vw, 68px);
    letter-spacing: -0.06em;
    font-weight: 450;
    line-height: 1.05;
  }
  .preview-label {
    display: block;
    color: var(--muted);
    font-size: 12px;
    margin-top: 12px;
  }
  .preview-sizes .size-bubbles {
    min-height: 0;
    gap: 5px;
    padding: 20px 0 0;
  }
  .preview-sizes .size-bubbles span {
    font-size: 9px;
    margin-top: 8px;
  }
  @media (max-width: 760px) {
    .story-grid {
      grid-template-columns: 1fr;
      gap: 35px;
    }
  }
</style>
