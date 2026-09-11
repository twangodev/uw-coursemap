<script lang="ts">
  import { LineChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX } from "d3-shape";
  import { departmentName } from "$lib/departments";
  import { termName, courseUrl } from "$lib/format";
  import { subjectVolumes, type Academics } from "$lib/school-academics";
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
      <p class="eyebrow">The academic landscape</p>
      <h2 id="academic-landscape">What does Madison study?</h2>
      <p>
        {termName(academics.term)}{academics.term !== selectedTerm
          ? " · latest recorded grades before the selected term"
          : ""}. Follow a subject into its courses.
      </p>
    </div>
    <div class="landscape">
      <div><SchoolTreemap courses={academics.courses} bind:subject /></div>
      <div class="subject-list">
        <h3>The biggest slices</h3>
        {#each groups.slice(0, 7) as group}<button
            onclick={() => (subject = group.subject)}
            ><span>{departmentName(group.subject)}</span><strong
              >{(
                (group.count /
                  academics.courses.reduce((n, c) => n + c.count, 0)) *
                100
              ).toFixed(1)}%</strong
            ></button
          >{/each}
        <p class="note">
          Share of recorded letter grades. Cross-listed courses split their
          volume evenly across subjects, so the pieces add up to the whole.
        </p>
      </div>
    </div>
    <div class="heading subheading">
      <h2>Every course is a dot</h2>
      <p>Find a familiar course—or something you’ve never heard of.</p>
    </div>
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
    <div class="heading subheading">
      <h2>Campus mainstays</h2>
      <p>
        How the eight courses with the most letter grades in {termName(
          academics.term,
        )} ranked across the last {history.length} recorded terms.
      </p>
    </div>
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
  </section>
{/if}

<style>
  .academics {
    margin-top: 80px;
  }
  .heading {
    margin-bottom: 30px;
  }
  .eyebrow {
    font-size: 12px;
    color: var(--accent);
    margin: 0 0 12px;
    letter-spacing: 0.04em;
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
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
    gap: 45px;
  }
  .landscape > div {
    min-width: 0;
  }
  .subject-list h3 {
    font-size: 16px;
    font-weight: 500;
    margin: 0 0 20px;
  }
  .subject-list button {
    display: flex;
    width: 100%;
    justify-content: space-between;
    gap: 15px;
    text-align: left;
    background: none;
    border: 0;
    border-bottom: 1px solid var(--border);
    padding: 13px 0;
    font: 13px var(--font-sans);
    color: var(--text);
    cursor: pointer;
  }
  .subject-list strong {
    font-weight: 500;
    color: var(--accent);
  }
  .note {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.6;
  }
  .subheading {
    margin-top: 65px;
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
    .subheading {
      margin-top: 50px;
    }
  }
</style>
