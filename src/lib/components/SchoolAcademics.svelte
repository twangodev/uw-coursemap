<script lang="ts">
  import { LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { hierarchy, treemap } from "d3-hierarchy";
  import { curveMonotoneX, line } from "d3-shape";
  import { departmentName } from "$lib/departments";
  import { termName, courseUrl } from "$lib/format";
  import { subjectVolumes, type Academics } from "$lib/school-academics";
  import StatsCard from "./StatsCard.svelte";
  import { gradeBands } from "$lib/school-sankey";
  import SchoolSankey from "./SchoolSankey.svelte";
  import SchoolTreemap from "./SchoolTreemap.svelte";
  import SchoolCourseDots from "./SchoolCourseDots.svelte";
  import Select from "./Select.svelte";
  let {
    academics,
    selectedTerm,
  }: { academics: Academics; selectedTerm: string } = $props();
  let subject = $state("");
  let selected = $derived(
    academics.courses.some((c) => c.subjects.includes(subject)) ? subject : "",
  );
  let groups = $derived(subjectVolumes(academics.courses));
  let filtered = $derived(
    selected
      ? academics.courses.filter((c) => c.subjects.includes(selected))
      : academics.courses,
  );
  const colors = [
    "#bd5047",
    "#3f927c",
    "#a881bd",
    "#cd923e",
    "#5086a5",
    "#b8668b",
    "#879653",
    "#9b8070",
  ];
  let history = $derived(
    academics.popularity[0]?.points.map((p, i) =>
      Object.assign(
        { term: termName(p.term) },
        ...academics.popularity.map((c) => ({
          [c.code]: c.points[i]?.rank ?? null,
        })),
      ),
    ) ?? [],
  );
  let rankMax = $derived(
    Math.max(
      10,
      ...academics.popularity.flatMap((c) => c.points.map((p) => p.rank ?? 0)),
    ),
  );
  type SubjectTile = { count: number; children?: SubjectTile[] };
  let tiles = $derived(
    treemap<SubjectTile>()
      .size([720, 220])
      .paddingInner(3)(
        hierarchy<SubjectTile>({ count: 0, children: groups })
          .sum((d) => d.count)
          .sort((a, b) => (b.value ?? 0) - (a.value ?? 0)),
      )
      .leaves(),
  );
  let dots = $derived(
    academics.courses.filter((c) => c.gpa !== null && c.count >= 30),
  );
  let largest = $derived(Math.max(1, ...dots.map((c) => c.count)));
  let bands = $derived(
    gradeBands.map((b) => ({
      ...b,
      count: academics.courses.reduce(
        (sum, c) => sum + b.indices.reduce((n, i) => n + c.grades[i], 0),
        0,
      ),
    })),
  );
  let total = $derived(bands.reduce((sum, b) => sum + b.count, 0));
  let paths = $derived(
    academics.popularity.map((c) =>
      line<{ rank: number | null }>()
        .defined((d) => d.rank !== null)
        .x((d, i) => 10 + (i / Math.max(1, c.points.length - 1)) * 300)
        .y((d) => 12 + (((d.rank ?? 1) - 1) / Math.max(1, rankMax - 1)) * 175)
        .curve(curveMonotoneX)(c.points),
    ),
  );
  let active = $state("");
</script>

{#if academics.term}
  <StatsCard title="What Madison studies" span={8}>
    {#snippet preview()}
      <svg
        class="tile-preview"
        viewBox="0 0 720 220"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {#each tiles as tile, i}<rect
            x={tile.x0}
            y={tile.y0}
            width={tile.x1 - tile.x0}
            height={tile.y1 - tile.y0}
            rx="2"
            fill={`color-mix(in srgb, var(--accent) ${25 + (i % 6) * 10}%, var(--surface))`}
          />{/each}
      </svg>
      <span class="preview-caption"
        >{groups.length} subjects · {termName(academics.term!)}</span
      >
    {/snippet}
    <p class="period">
      {termName(academics.term!)} · select a subject to explore.
    </p>
    <SchoolTreemap courses={academics.courses} bind:subject />
  </StatsCard>
  <StatsCard title="Popular courses over time" span={4}>
    {#snippet preview()}
      <svg class="mini-chart" viewBox="0 0 320 200" aria-hidden="true"
        >{#each paths as path, i}<path
            d={path ?? undefined}
            fill="none"
            stroke={colors[i]}
            stroke-width="2"
          />{/each}</svg
      >
      <span class="preview-caption">{history.length} recorded semesters</span>
    {/snippet}
    <p class="period">
      The eight largest courses in {termName(academics.term!)} across the last {history.length}
      recorded terms.
    </p>
    {#if history.length > 1}<div class="rank-chart">
        <LineChart
          data={history}
          x="term"
          xScale={scalePoint()}
          yDomain={[rankMax, 1]}
          yNice={false}
          series={academics.popularity.map((c, i) => ({
            key: c.code,
            label: c.code,
            color: colors[i],
            props: {
              strokeWidth: !active || active === c.code ? 2.5 : 1,
              opacity: !active || active === c.code ? 1 : 0.18,
            },
          }))}
          height={340}
          legend={false}
          props={{
            xAxis: { tickOcclusion: true, tickSpacing: 100 },
            yAxis: { label: "Rank by recorded letter grades" },
            spline: { curve: curveMonotoneX },
            points: { r: 3 },
            tooltip: {
              hideTotal: true,
              item: { format: (v: number) => `#${v}` },
            },
          }}
        />
      </div>{/if}
    <div class="rank-legend">
      {#each academics.popularity as course, i}<div>
          <button
            style={`--series:${colors[i]}`}
            aria-pressed={active === course.code}
            onclick={() => (active = active === course.code ? "" : course.code)}
            ><i></i>{course.code}</button
          ><a href={courseUrl(course.code)} aria-label={`Open ${course.code}`}
            >↗</a
          >
        </div>{/each}
    </div>
    <p class="note">
      Rank 1 is the largest recorded letter-grade count. Ties use course code
      order. Gaps mean no recorded letter grades, not zero enrollment.
    </p>
  </StatsCard>
  <StatsCard title="Grade flows" span={6}>
    {#snippet preview()}
      <svg class="flow-preview" viewBox="0 0 420 200" aria-hidden="true">
        {#each bands as band, i}<path
            d={`M15,100 C190,100 230,${28 + i * 48} 405,${28 + i * 48}`}
            fill="none"
            stroke={band.color}
            stroke-width={total ? (band.count / total) * 88 : 0}
            opacity="0.7"
          />{/each}
      </svg>
      <span class="preview-caption">Departments → courses → grades</span>
    {/snippet}
    <SchoolSankey {academics} {selectedTerm} />
  </StatsCard>
  <StatsCard title="Find your course" span={6}>
    {#snippet preview()}
      <svg class="mini-chart" viewBox="0 0 420 200" aria-hidden="true"
        >{#each dots as course}<circle
            cx={10 + (course.gpa! / 4) * 400}
            cy={188 - (Math.log1p(course.count) / Math.log1p(largest)) * 175}
            r="1.4"
            fill="var(--accent)"
            opacity="0.55"
          />{/each}</svg
      >
      <span class="preview-caption"
        >{dots.length.toLocaleString()} courses with 30+ letter grades</span
      >
    {/snippet}
    <p class="period">{termName(academics.term!)} · recorded letter grades</p>
    <div class="subject-filter">
      <Select
        value={selected}
        options={[
          { value: "", label: "All subjects" },
          ...groups.map((g) => ({
            value: g.subject,
            label: departmentName(g.subject),
          })),
        ]}
        label="Dot plot subject"
        onChange={(value) => (subject = value)}
      />{#if selected}<span>{departmentName(selected)}</span>{/if}
    </div>
    <SchoolCourseDots courses={filtered} />
  </StatsCard>
{/if}

<style>
  .tile-preview {
    width: 100%;
    flex: 1;
    min-height: 0;
  }
  .mini-chart,
  .flow-preview {
    width: 100%;
    height: 180px;
    display: block;
  }
  .preview-caption,
  .period {
    color: var(--muted);
    font-size: 12px;
    margin-top: 16px;
  }
  .period {
    margin: 0 0 20px;
  }
  .note {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.6;
  }
  .subject-filter {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 22px;
    font-size: 12px;
    color: var(--muted);
  }
  .rank-legend {
    display: flex;
    gap: 12px 24px;
    flex-wrap: wrap;
    margin: 15px 0;
  }
  .rank-legend > div {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .rank-legend button {
    display: flex;
    gap: 7px;
    align-items: center;
    font: 12px var(--font-sans);
    color: var(--text);
    padding: 4px 0;
    border: 0;
    background: none;
    cursor: pointer;
  }
  .rank-legend button[aria-pressed="true"] {
    text-decoration: underline;
  }
  .rank-legend i {
    width: 14px;
    height: 3px;
    background: var(--series);
  }
  .rank-legend a {
    font-size: 13px;
    color: var(--muted);
  }
</style>
