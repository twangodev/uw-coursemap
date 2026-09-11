<script lang="ts">
  import { LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX } from "d3-shape";
  import { departmentName } from "$lib/departments";
  import { termName, courseUrl } from "$lib/format";
  import { subjectVolumes, type Academics } from "$lib/school-academics";
  import StatsDisclosure from "./StatsDisclosure.svelte";
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
  let active = $state("");
</script>

{#if academics.term}
  <section class="academics" aria-labelledby="academic-landscape">
    <div class="heading">
      <h2 id="academic-landscape">What Madison studies.</h2>
      <p>{termName(academics.term)} · select a subject to explore.</p>
    </div>
    <div class="landscape">
      <div><SchoolTreemap courses={academics.courses} bind:subject /></div>
    </div>
    <div class="explore-more">
      <StatsDisclosure
        title="Grade flows"
        description="Departments → courses → grades"
      >
        <SchoolSankey {academics} {selectedTerm} />
      </StatsDisclosure>
      <StatsDisclosure
        title="Find your course"
        description="Compare size and grades"
      >
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
      </StatsDisclosure>
      <StatsDisclosure
        title="Popular courses over time"
        description="The largest courses, across semesters"
      >
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
                onclick={() =>
                  (active = active === course.code ? "" : course.code)}
                ><i></i>{course.code}</button
              ><a
                href={courseUrl(course.code)}
                aria-label={`Open ${course.code}`}>↗</a
              >
            </div>{/each}
        </div>
        <p class="note">
          Rank 1 is the largest recorded letter-grade count. Ties use course
          code order. Gaps mean no recorded letter grades, not zero enrollment.
        </p>
      </StatsDisclosure>
    </div>
  </section>
{/if}

<style>
  .academics {
    margin-top: 100px;
  }
  .heading {
    margin-bottom: 30px;
  }
  h2 {
    font-size: clamp(28px, 3.5vw, 42px);
    letter-spacing: -0.045em;
    font-weight: 500;
    margin: 0 0 12px;
  }
  .heading > p:last-child {
    color: var(--muted);
    line-height: 1.6;
    max-width: 780px;
  }
  .landscape {
    display: grid;
    grid-template-columns: 1fr;
    gap: 45px;
  }
  .landscape > div {
    min-width: 0;
  }
  .note {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.6;
  }
  .explore-more {
    margin-top: 40px;
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
  @media (max-width: 760px) {
    .landscape {
      grid-template-columns: 1fr;
      gap: 22px;
    }
    .academics {
      margin-top: 60px;
    }
  }
</style>
