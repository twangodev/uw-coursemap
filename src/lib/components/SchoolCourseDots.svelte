<script lang="ts">
  import { tick } from "svelte";
  import { Chart, Points } from "layerchart";
  import { scaleSymlog } from "d3-scale";
  import { courseUrl, courseTitle, normalize } from "$lib/format";
  import type { AcademicCourse } from "$lib/school-academics";
  let { courses }: { courses: AcademicCourse[] } = $props();
  const id = $props.id();
  let search = $state("");
  let selected = $state("");
  let filtered = $derived(
    courses.filter(
      (c) =>
        c.gpa !== null &&
        c.count >= 30 &&
        (!search ||
          normalize(c.code).includes(normalize(search)) ||
          (search.trim().toLowerCase() === "cs" &&
            c.subjects.includes("COMPSCI")) ||
          c.title.toLowerCase().includes(search.toLowerCase())),
    ),
  );
  let focus = $derived(
    filtered.find((c) => c.code === selected) ?? filtered[0],
  );
</script>

<div class="flex justify-between gap-5 items-end mb-[15px] dot-controls">
  <label class="flex flex-col gap-2 text-[12px]"
    >Find a course<input
      class="text-foreground bg-surface border border-border rounded-control max-w-full w-65 py-2 px-2.5"
      type="search"
      bind:value={search}
      placeholder="CS, calculus, music…"
      aria-label="Find a course in the dot plot"
    /></label
  ><span class="text-[12px] text-muted"
    >{filtered.length.toLocaleString()} courses · 30+ letter grades</span
  >
</div>
{#if filtered.length}
  <div
    class="min-w-0 dot-chart"
    aria-label="Course GPA versus recorded letter-grade count"
  >
    <Chart
      data={filtered}
      x="gpa"
      y="count"
      xDomain={[0, 4]}
      yScale={scaleSymlog()}
      height={330}
      padding={{ left: 55, right: 15, top: 15, bottom: 35 }}
      axis={true}
      grid={{ x: false, y: true }}
      tooltipContext={false}
      props={{
        xAxis: { label: "Course GPA" },
        yAxis: { label: "Recorded letter grades", tickSpacing: 65 },
      }}
    >
      {#snippet marks()}
        <Points>
          {#snippet children({ points })}
            {#each points as point, i}
              <circle
                cx={point.x}
                cy={point.y}
                r={point.data.code === focus?.code ? 6 : 3.5}
                fill="var(--accent)"
                fill-opacity={point.data.code === focus?.code ? 1 : 0.42}
                stroke={point.data.code === focus?.code
                  ? "var(--text)"
                  : "none"}
                role="button"
                id={`${id}-${i}`}
                tabindex={point.data.code === focus?.code ? 0 : -1}
                aria-label={`${point.data.code}: GPA ${point.data.gpa.toFixed(2)}, ${point.data.count} letter grades`}
                onpointerenter={() => (selected = point.data.code)}
                onfocus={() => (selected = point.data.code)}
                onclick={() => (selected = point.data.code)}
                onkeydown={async (e) => {
                  if (
                    [
                      "ArrowLeft",
                      "ArrowRight",
                      "ArrowUp",
                      "ArrowDown",
                    ].includes(e.key)
                  ) {
                    e.preventDefault();
                    const next =
                      (i +
                        (["ArrowRight", "ArrowDown"].includes(e.key) ? 1 : -1) +
                        points.length) %
                      points.length;
                    selected = points[next].data.code;
                    await tick();
                    document.getElementById(`${id}-${next}`)?.focus();
                  }
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selected = point.data.code;
                  }
                }}
              />
            {/each}
          {/snippet}
        </Points>
      {/snippet}
    </Chart>
  </div>
  <div
    class="flex flex-col gap-2 min-h-[65px] text-[14px] mt-4 dot-detail"
    aria-live="polite"
  >
    {#if focus}<a href={courseUrl(focus.code)}
        ><strong class="font-[550] mr-2">{focus.code}</strong>
        {courseTitle(focus.title)} ↗</a
      ><span class="text-[12px] text-muted"
        >{focus.gpa?.toFixed(2)} GPA · {focus.count.toLocaleString()} recorded letter
        grades</span
      >{/if}
  </div>
{:else}<p class="text-[12px] text-muted empty">
    No matching courses with at least 30 letter grades.
  </p>{/if}
<p class="text-[12px] text-muted leading-[1.6] mt-2 note">
  Each dot is one course. The vertical scale is compressed so smaller courses
  remain visible. Select a dot, then follow its course link. Arrow keys move
  between focused dots.
</p>

<style>
  .dot-controls input {
    font: 14px var(--font-sans);
  }
  .dot-chart :global(circle) {
    cursor: pointer;
  }
  .dot-chart :global(circle:focus-visible) {
    outline: none;
    stroke: var(--text);
    stroke-width: 2;
  }
  @media (max-width: 640px) {
    .dot-controls {
      align-items: start;
      flex-direction: column;
      gap: 10px;
    }
    .dot-controls label {
      width: 100%;
    }
    .dot-controls input {
      width: 100%;
    }
  }
</style>
