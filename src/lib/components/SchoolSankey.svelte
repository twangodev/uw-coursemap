<script lang="ts">
  import { Chart } from "layerchart";
  import { Sankey } from "layerchart/graph";
  import { departmentName } from "$lib/departments";
  import { courseUrl, termName } from "$lib/format";
  import { subjectVolumes, type Academics } from "$lib/school-academics";
  import { gradeFlow, type FlowNode } from "$lib/school-sankey";
  import Select from "./Select.svelte";

  let {
    academics,
    selectedTerm,
  }: { academics: Academics; selectedTerm: string } = $props();
  let subject = $state("");
  let active = $state("");
  let detail = $state("");
  let graph = $derived(gradeFlow(academics.courses, subject));
  let groups = $derived(subjectVolumes(academics.courses));
  const number = (value: number) =>
    value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  const label = (node: FlowNode) =>
    node.subject ? departmentName(node.subject) : node.label;
  function select(value: string) {
    subject = value;
    active = "";
    detail = "";
  }
  function inspect(node: FlowNode, value: number) {
    active = node.id;
    detail = `${label(node as FlowNode)} · ${number(value)} attributed letter grades`;
  }
  function clear() {
    active = "";
    detail = "";
  }
</script>

<section class="grade-flow" aria-labelledby="grade-flow-heading">
  <div class="heading">
    <h2 id="grade-flow-heading">Follow the grades</h2>
    <p>From departments, through courses, to the grades students received.</p>
  </div>
  <div class="toolbar">
    <Select
      value={subject}
      options={[
        { value: "", label: "All departments" },
        ...groups.map((g) => ({
          value: g.subject,
          label: departmentName(g.subject),
        })),
      ]}
      label="Grade flow department"
      onChange={select}
    />
    {#if subject}<button class="reset" onclick={() => select("")}
        >← All departments</button
      >{/if}
    <span
      >{academics.term
        ? termName(academics.term)
        : "No recorded term"}{academics.term !== selectedTerm
        ? " · latest recorded grades"
        : ""}</span
    >
  </div>
  {#if graph.links.length}
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users must be able to scroll this chart.) -->
    <div
      class="flow-scroll"
      tabindex="0"
      role="region"
      aria-label="Department to course to grade-band Sankey. Scroll horizontally on narrow screens."
    >
      <div class="flow-chart">
        <div class="columns" aria-hidden="true">
          <span>Department</span><span>Course</span><span>Grade band</span>
        </div>
        <Chart
          data={graph}
          height={440}
          padding={{ left: 12, right: 65, top: 8, bottom: 8 }}
          axis={false}
          grid={false}
          tooltipContext={false}
        >
          {#snippet marks()}
            <Sankey
              nodeId={(n) => n.id}
              nodeWidth={8}
              nodePadding={19}
              nodeSort={(a, b) =>
                a.kind === "grade" ? a.id.localeCompare(b.id) : undefined}
            >
              {#snippet children({ nodes, links })}
                <g>
                  {#each links as link}
                    {@const related =
                      !active ||
                      link.source.id === active ||
                      link.target.id === active}
                    {@const mid = (link.source.x1 + link.target.x0) / 2}
                    <path
                      d={`M${link.source.x1},${link.y0}C${mid},${link.y0} ${mid},${link.y1} ${link.target.x0},${link.y1}`}
                      fill="none"
                      stroke={link.target.kind === "grade"
                        ? link.target.color
                        : "#bd5047"}
                      stroke-width={Math.max(0.5, link.width)}
                      opacity={related ? (active ? 0.65 : 0.24) : 0.05}
                      class="flow-link"
                    >
                      <title
                        >{label(link.source)} → {label(link.target)}: {number(
                          link.value!,
                        )} attributed letter grades</title
                      >
                    </path>
                  {/each}
                  {#each nodes as node}
                    {@const height = Math.max(1, node.y1! - node.y0!)}
                    {@const y = (node.y0! + node.y1!) / 2}
                    {#snippet mark()}
                      <rect
                        x={node.x0}
                        y={node.y0}
                        width={8}
                        {height}
                        rx={2}
                        fill={node.color}
                      />
                      <text x={node.x1! + 7} {y} dominant-baseline="middle"
                        >{node.label}</text
                      >
                    {/snippet}
                    {#if node.subject}
                      <g
                        role="button"
                        tabindex="0"
                        aria-label={`Explore ${label(node as FlowNode)} grade flow`}
                        onclick={() => select(node.subject)}
                        onkeydown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            select(node.subject);
                          }
                        }}
                        onpointerenter={() =>
                          inspect(node as FlowNode, node.value!)}
                        onpointerleave={clear}
                        onfocus={() => inspect(node as FlowNode, node.value!)}
                        onblur={clear}
                      >
                        <title
                          >{label(node as FlowNode)} · {number(node.value!)} attributed
                          letter grades. Click to explore courses.</title
                        >
                        {@render mark()}
                      </g>
                    {:else if node.code}
                      <a
                        href={courseUrl(node.code)}
                        aria-label={`Open ${node.code}`}
                        onpointerenter={() =>
                          inspect(node as FlowNode, node.value!)}
                        onpointerleave={clear}
                        onfocus={() => inspect(node as FlowNode, node.value!)}
                        onblur={clear}
                      >
                        <title
                          >{node.label} · {number(node.value!)} attributed letter
                          grades</title
                        >
                        {@render mark()}
                      </a>
                    {:else}
                      <g
                        tabindex="0"
                        role="button"
                        onclick={() => inspect(node as FlowNode, node.value!)}
                        onkeydown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            inspect(node as FlowNode, node.value!);
                          }
                        }}
                        aria-label={`${node.label}: ${number(node.value!)} attributed letter grades`}
                        onpointerenter={() =>
                          inspect(node as FlowNode, node.value!)}
                        onpointerleave={clear}
                        onfocus={() => inspect(node as FlowNode, node.value!)}
                        onblur={clear}
                      >
                        {@render mark()}
                      </g>
                    {/if}
                  {/each}
                </g>
              {/snippet}
            </Sankey>
          {/snippet}
        </Chart>
      </div>
    </div>
    <p class="flow-detail" aria-live="polite">
      {detail ||
        `${number(graph.total)} attributed letter grades across ${number(graph.courseCount)} courses`}
    </p>
    <p class="note">
      Width represents recorded letter grades, not unique students. Cross-listed
      courses split their weight evenly across departments. The eight largest
      courses{subject ? "" : " and six largest departments"} are shown individually;
      “Other” retains the rest. Choose a department to explore, or a course to open
      it.<span class="mobile-note">
        Swipe the chart to see all three columns.</span
      >
    </p>
  {:else}
    <p class="note">No recorded letter grades for this selection.</p>
  {/if}
</section>

<style>
  .grade-flow {
    margin-top: 65px;
    min-width: 0;
  }
  .heading {
    margin-bottom: 26px;
  }
  h2 {
    font-size: clamp(28px, 3.5vw, 42px);
    letter-spacing: -0.045em;
    font-weight: 500;
    margin: 0 0 12px;
  }
  .heading p {
    color: var(--muted);
    line-height: 1.6;
  }
  .toolbar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 26px;
  }
  .toolbar > span {
    margin-left: auto;
    font-size: 12px;
    color: var(--muted);
  }
  .reset {
    border: 0;
    background: none;
    color: var(--muted);
    font: 12px var(--font-sans);
    padding: 4px 0;
    cursor: pointer;
  }
  .flow-scroll {
    overflow-x: auto;
  }
  .flow-chart {
    min-width: 670px;
  }
  .columns {
    display: flex;
    justify-content: space-between;
    padding: 0 10px 12px;
    color: var(--muted);
    font-size: 11px;
  }
  .columns span:nth-child(2) {
    transform: translateX(-15px);
  }
  .flow-chart :global(text) {
    font: 11px var(--font-sans);
    fill: var(--text);
    paint-order: stroke;
    stroke: var(--bg);
    stroke-width: 4px;
    stroke-linejoin: round;
  }
  .flow-chart :global([role="button"]),
  .flow-chart :global(a) {
    cursor: pointer;
  }
  .flow-chart :global(g:focus-visible rect),
  .flow-chart :global(a:focus-visible rect) {
    stroke: var(--text);
    stroke-width: 2px;
  }
  .flow-link {
    transition: opacity 160ms ease;
  }
  .flow-detail {
    font-size: 13px;
    margin: 18px 0 8px;
    min-height: 1.6em;
    line-height: 1.6;
  }
  .note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.7;
    max-width: 850px;
  }
  .mobile-note {
    display: none;
  }
  @media (max-width: 760px) {
    .grade-flow {
      margin-top: 50px;
    }
    .toolbar > span {
      width: 100%;
      margin-left: 0;
    }
    .mobile-note {
      display: inline;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .flow-link {
      transition: none;
    }
  }
</style>
