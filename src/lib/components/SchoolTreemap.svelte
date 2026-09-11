<script lang="ts">
  import { Chart } from "layerchart";
  import { Treemap } from "layerchart/hierarchy";
  import { hierarchy } from "d3-hierarchy";
  import { departmentName } from "$lib/departments";
  import { courseUrl, courseTitle } from "$lib/format";
  import { subjectVolumes, type AcademicCourse } from "$lib/school-academics";
  let {
    courses,
    subject = $bindable(""),
  }: { courses: AcademicCourse[]; subject?: string } = $props();
  type Tile = {
    label: string;
    value?: number;
    code?: string;
    subject?: string;
    children?: Tile[];
  };
  let groups = $derived(subjectVolumes(courses));
  let root = $derived(
    hierarchy<Tile>({
      label: "UW–Madison",
      children: subject
        ? courses
            .filter((c) => c.subjects.includes(subject))
            .map((c) => ({
              label: c.code,
              value: c.count / c.subjects.length,
              code: c.code,
            }))
        : groups.map((g) => ({
            label: departmentName(g.subject),
            value: g.count,
            subject: g.subject,
          })),
    })
      .sum((d) => d.value ?? 0)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0)),
  );
  let selected = $state("");
</script>

<div class="tree-toolbar">
  <span>{subject ? departmentName(subject) : "All subjects"}</span
  >{#if subject}<button
      onclick={() => {
        subject = "";
        selected = "";
      }}>← All subjects</button
    >{/if}
</div>
<div
  class="treemap"
  aria-label="Subjects sized by recorded letter-grade volume"
>
  <Chart
    height={380}
    padding={0}
    axis={false}
    grid={false}
    tooltipContext={false}
  >
    {#snippet marks()}
      <Treemap hierarchy={root} paddingInner={3}>
        {#snippet children({ nodes })}
          {#each nodes.filter((n) => !n.children) as node, i}
            {@const width = node.x1 - node.x0}{@const height =
              node.y1 - node.y0}
            <g transform={`translate(${node.x0},${node.y0})`}>
              {#if node.data.code}
                <a
                  href={courseUrl(node.data.code)}
                  aria-label={`${node.data.label}: ${Math.round(node.value ?? 0).toLocaleString()} attributed letter grades`}
                  onpointerenter={() =>
                    (selected = `${node.data.label} · ${courseTitle(courses.find((c) => c.code === node.data.code)?.title ?? "")}`)}
                  onfocus={() => (selected = node.data.label)}
                  ><rect
                    {width}
                    {height}
                    rx="3"
                    fill={`color-mix(in srgb, var(--accent) ${30 + (i % 5) * 12}%, var(--surface))`}
                  />{#if width > 56 && height > 25}<text
                      x="8"
                      y="18"
                      fill="var(--text)">{node.data.label}</text
                    >{/if}</a
                >
              {:else}
                <g
                  role="button"
                  tabindex="0"
                  aria-label={`Explore ${node.data.label}`}
                  onclick={() => {
                    subject = node.data.subject!;
                    selected = "";
                  }}
                  onkeydown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      subject = node.data.subject!;
                      selected = "";
                    }
                  }}
                  onpointerenter={() =>
                    (selected = `${node.data.label} · ${Math.round(node.value ?? 0).toLocaleString()} attributed letter grades`)}
                  onfocus={() =>
                    (selected = `${node.data.label} · ${Math.round(node.value ?? 0).toLocaleString()} attributed letter grades`)}
                >
                  <rect
                    {width}
                    {height}
                    rx="3"
                    fill={`color-mix(in srgb, var(--accent) ${22 + (i % 6) * 9}%, var(--surface))`}
                  />{#if width > 48 && height > 25}<svg {width} {height}
                      ><text x="8" y="19" fill="var(--text)"
                        >{node.data.subject}</text
                      >{#if height > 48 && width > 95}<text
                          x="8"
                          y="38"
                          class="tile-count"
                          fill="var(--text)"
                          >{Math.round(node.value ?? 0).toLocaleString()}</text
                        >{/if}</svg
                    >{/if}
                </g>
              {/if}
            </g>
          {/each}
        {/snippet}
      </Treemap>
    {/snippet}
  </Chart>
</div>
<p class="tree-detail" aria-live="polite">
  {selected ||
    "Select a subject to zoom into its courses. Larger tiles mean more recorded letter grades."}
</p>

<style>
  .tree-toolbar {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    font-size: 13px;
    margin: 0 0 18px;
    min-height: 25px;
    align-items: center;
  }
  .tree-toolbar button {
    background: none;
    border: 0;
    color: var(--accent);
    cursor: pointer;
    padding: 0;
    font: inherit;
  }
  .treemap {
    width: 100%;
    min-width: 0;
  }
  .treemap :global(text) {
    font: 12px var(--font-sans);
    pointer-events: none;
  }
  .treemap :global(.tile-count) {
    font-size: 11px;
    opacity: 0.8;
  }
  .treemap :global(rect) {
    stroke: transparent;
    cursor: pointer;
    transition: stroke 120ms;
  }
  .treemap :global(g[role="button"]:focus-visible),
  .treemap :global(a:focus-visible) {
    outline: none;
  }
  .treemap :global(g[role="button"]:focus-visible rect),
  .treemap :global(a:focus-visible rect),
  .treemap :global(g[role="button"]:hover rect),
  .treemap :global(a:hover rect) {
    stroke: var(--text);
    stroke-width: 2;
  }
  .tree-detail {
    font-size: 12px;
    color: var(--muted);
    min-height: 3em;
    line-height: 1.5;
    margin: 16px 0 0;
  }
  @media (prefers-reduced-motion: reduce) {
    .treemap :global(rect) {
      transition: none;
    }
  }
</style>
