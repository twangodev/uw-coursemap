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

<div class="dot-controls">
  <label
    >Find a course<input
      type="search"
      bind:value={search}
      placeholder="CS, calculus, music…"
      aria-label="Find a course in the dot plot"
    /></label
  ><span>{filtered.length.toLocaleString()} courses · 30+ letter grades</span>
</div>
{#if filtered.length}
  <div
    class="dot-chart"
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
  <div class="dot-detail" aria-live="polite">
    {#if focus}<a href={courseUrl(focus.code)}
        ><strong>{focus.code}</strong> {courseTitle(focus.title)} ↗</a
      ><span
        >{focus.gpa?.toFixed(2)} GPA · {focus.count.toLocaleString()} recorded letter
        grades</span
      >{/if}
  </div>
{:else}<p class="empty">
    No matching courses with at least 30 letter grades.
  </p>{/if}
<p class="note">
  Each dot is one course. The vertical scale is compressed so smaller courses
  remain visible. Select a dot, then follow its course link. Arrow keys move
  between focused dots.
</p>

<style>
  .dot-controls {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    align-items: end;
    margin-bottom: 15px;
  }
  .dot-controls label {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 12px;
  }
  .dot-controls input {
    font: 14px var(--font-sans);
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 8px 10px;
    max-width: 100%;
    width: 260px;
  }
  .dot-controls > span,
  .note,
  .empty {
    font-size: 12px;
    color: var(--muted);
  }
  .dot-chart {
    min-width: 0;
  }
  .dot-chart :global(circle) {
    cursor: pointer;
  }
  .dot-chart :global(circle:focus-visible) {
    outline: none;
    stroke: var(--text);
    stroke-width: 2;
  }
  .dot-detail {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-height: 65px;
    font-size: 14px;
    margin-top: 16px;
  }
  .dot-detail strong {
    font-weight: 550;
    margin-right: 8px;
  }
  .dot-detail > span {
    font-size: 12px;
    color: var(--muted);
  }
  .note {
    line-height: 1.6;
    margin-top: 8px;
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
