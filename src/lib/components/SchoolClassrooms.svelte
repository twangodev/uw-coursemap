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
    <strong
      class="block text-[clamp(40px,_4.5vw,_68px)] tracking-[-0.06em] font-[450] leading-[1.05] preview-number"
      ><AnimatedNumber
        value={classroom.medianLecture}
        decimals={classroom.medianLecture && classroom.medianLecture % 1
          ? 1
          : 0}
      /></strong
    >
    <span class="block text-muted text-[12px] mt-3 preview-label"
      >{historicalClassroom
        ? "median outcomes per graded section"
        : "median lecture enrollment"}</span
    >
    <div class="preview-sizes">
      <div
        class="grid grid-cols-6 items-end gap-[5px] min-h-0 pt-5 pb-0 size-bubbles px-0"
        role="img"
        aria-label="Section size distribution. Circle area represents the number of sections."
      >
        {#each classroom.sizes as size}
          <div>
            <svg class="block w-full" viewBox="0 0 100 100" aria-hidden="true"
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
            ><span class="block text-center text-[9px] text-muted mt-2"
              >{size.label}</span
            >
          </div>
        {/each}
      </div>
    </div>
    {#if under50 !== null}<span
        class="block text-muted text-[11px] mt-3.5 tabular-nums preview-math"
        >{under50.toFixed(1)}% of sections under 50</span
      >{/if}
  {/snippet}
  {#if classroom.knownLectures}
    <div
      class="grid grid-cols-[minmax(0,_1fr)_minmax(0,_1.35fr)] gap-[clamp(28px,_5vw,_70px)] items-start story-grid classroom"
    >
      <div class="min-w-0">
        <p
          class="text-[42px] leading-[1.1] tracking-[-0.02em] max-w-107.5 mt-0 mb-6.5 observation mx-0"
        >
          <strong class="font-medium text-foreground"
            ><AnimatedNumber
              value={classroom.medianLecture}
              decimals={classroom.medianLecture! % 1 ? 1 : 0}
            />
          </strong>
          <span
            class="block text-[13px] text-muted mt-2.5 tracking-[0] observation-label"
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

        <details class="mt-[25px] text-[13px] disclosure">
          <summary>Section sizes & coverage</summary>
          <p class="text-muted text-[12px] leading-[1.6] coverage">
            {#if historicalClassroom}Based on {current.gradedSections.toLocaleString()}
              section grade records, including non-letter outcomes. These are recorded
              outcomes, not historical enrollment snapshots; section type is unavailable.{:else}Known
              enrollment for {current.knownLectures.toLocaleString()}
              of {current.lectures.toLocaleString()}
              lecture sections. Labs and discussions excluded.{/if}
          </p>

          <div class="mt-4 max-h-80 overflow-auto grade-table">
            {#each classroom.sizes as size}<div
                class="flex justify-between gap-5 py-2 px-0"
              >
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
            {#each current.largest as course, i}<a
                class="flex items-center gap-[15px] border-b border-b-border py-[15px] px-0"
                href={courseUrl(course.code)}
                ><span class="text-[12px] text-muted rank">{i + 1}</span><span
                  class="flex min-w-0 flex-col gap-[5px] course"
                  ><strong class="text-[13px] font-medium">{course.code}</strong
                  ><span class="text-[13px] text-muted leading-[1.4]"
                    >{courseTitle(course.title)}</span
                  ></span
                ><span class="flex gap-2.5 items-center text-[14px] enrolled"
                  >{course.enrolled.toLocaleString()}<ArrowUpRight
                    size={14}
                  /></span
                ></a
              >{/each}
          </div></Disclosure
        >{/if}
    </div>
  {:else}<p class="text-muted leading-[1.7] max-w-145 empty py-7.5 px-0">
      Lecture enrollment isn’t available for this term. Historical grades are
      shown below where available.
    </p>{/if}
</StatsCard>

<style>
  .course {
    flex: 1;
  }
  @media (max-width: 760px) {
    .story-grid {
      grid-template-columns: 1fr;
      gap: 35px;
    }
  }
</style>
