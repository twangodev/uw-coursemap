<script lang="ts">
  import { BarChart, LineChart, AreaChart } from "layerchart";
  import { scalePoint } from "d3-scale";
  import { curveMonotoneX } from "d3-shape";
  import { goto } from "$app/navigation";
  import { ArrowUpRight, ChevronLeft, ChevronRight } from "@lucide/svelte";
  import Select from "$lib/components/Select.svelte";
  import AnimatedNumber from "$lib/components/AnimatedNumber.svelte";
  import SchoolAcademics from "$lib/components/SchoolAcademics.svelte";
  import SchoolBuildingMap from "$lib/components/SchoolBuildingMap.svelte";
  import { termName, courseUrl, courseTitle } from "$lib/format";
  import { gradedTerm, gradeLabels, type SchoolStats } from "$lib/school-stats";
  let { data } = $props();
  let stats: SchoolStats = $derived(data.schoolStats);
  let term = $derived(stats.selectedTerm);
  let terms = $derived(Object.keys(stats.terms).sort().reverse());
  let current = $derived(stats.terms[term]);
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
  const gradeColors = [
    "#38734d",
    "#68976d",
    "#91a77d",
    "#b3b38d",
    "#bc9a73",
    "#ba6958",
    "var(--accent)",
  ];
  let gradeMix = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => t <= term && r.gradeCount > 0)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([t, r]) =>
        Object.assign(
          { term: termName(t) },
          ...gradeLabels.map((g, i) => ({
            [g]: (r.grades[i] / r.gradeCount) * 100,
          })),
        ),
      ),
  );

  let index = $derived(terms.indexOf(term));
  let gradeTerm = $derived(gradedTerm(stats, term));
  let grades = $derived(gradeTerm ? stats.terms[gradeTerm] : null);
  let bars = $derived(
    gradeLabels.map((grade, i) => ({
      grade,
      percentage: grades?.gradeCount
        ? (grades.grades[i] / grades.gradeCount) * 100
        : 0,
    })),
  );
  let trend = $derived(
    Object.entries(stats.terms)
      .filter(([t, r]) => t <= term && r.gradeCount > 0)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([t, r]) => ({ term: termName(t), gpa: r.gpa })),
  );
  let domain = $derived(
    trend.length
      ? [
          Math.max(
            0,
            Math.floor((Math.min(...trend.map((r) => r.gpa!)) - 0.1) * 10) / 10,
          ),
          Math.min(
            4,
            Math.ceil((Math.max(...trend.map((r) => r.gpa!)) + 0.1) * 10) / 10,
          ),
        ]
      : [0, 4],
  );
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
  let popularGrade = $derived(
    grades
      ? gradeLabels[grades.grades.indexOf(Math.max(...grades.grades))]
      : "",
  );
  function changeTerm(value: string) {
    activeCell = null;
    goto(`/stats?term=${value}`, { noScroll: true, keepFocus: true });
  }
</script>

<div class="school-stats">
  <header class="intro">
    <div>
      <p class="eyebrow">Across UW–Madison</p>
      <h1>UW–Madison,<br />by the numbers.</h1>
      <p class="lede">
        Find the rhythm of the week, the shape of a classroom, and the grades
        behind it all.
      </p>
    </div>
    <div class="term-picker">
      <button
        aria-label="Previous term"
        disabled={index === terms.length - 1}
        onclick={() => changeTerm(terms[index + 1])}
        ><ChevronLeft size={15} /></button
      ><Select
        value={term}
        options={terms.map((t) => ({ value: t, label: termName(t) }))}
        label="Statistics term"
        onChange={changeTerm}
      /><button
        aria-label="Next term"
        disabled={index === 0}
        onclick={() => changeTerm(terms[index - 1])}
        ><ChevronRight size={15} /></button
      >
    </div>
  </header>
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

  {#if stats.academics}{#key term}<SchoolAcademics
        academics={stats.academics}
        selectedTerm={term}
      />{/key}{/if}

  <section aria-labelledby="rhythm">
    <div class="section-heading">
      <p class="eyebrow">01 / The week</p>
      <h2 id="rhythm">The rhythm of campus</h2>
      <p>{termName(term)} · scheduled teaching, in Madison time.</p>
    </div>
    {#if current.schedule.meetings}
      <div class="story-grid">
        <div class="heat-panel">
          <p class="observation">
            <strong>{weekdays[peak.day]} at {timeLabel(peak.hour)}</strong> is the
            busiest hour in the recorded schedule.
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
              the recorded term{:else}Explore an hour. Darker cells mean more
              scheduled meetings.{/if}
          </p>
          <p class="coverage">
            Recorded {current.schedule.from} – {current.schedule.through}.
            Includes meetings with known buildings and a matched term.
          </p>
        </div>
        <div><SchoolBuildingMap buildings={current.schedule.buildings} /></div>
      </div>
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
        We don’t have a building schedule for {termName(term)} in this dataset. Try
        the current term to explore campus activity.
      </p>{/if}
  </section>

  <section aria-labelledby="classroom">
    <div class="section-heading">
      <p class="eyebrow">02 / The classroom</p>
      <h2 id="classroom">Room for everyone</h2>
      <p>
        From a small seminar to a lecture hall. What does a UW classroom look
        like?
      </p>
    </div>
    {#if classroom.knownLectures}
      <div class="story-grid classroom">
        <div>
          <p class="observation">
            The middle of the pack? <strong
              ><AnimatedNumber
                value={classroom.medianLecture}
                decimals={classroom.medianLecture! % 1 ? 1 : 0}
              />
              {historicalClassroom ? "recorded outcomes" : "enrolled"}</strong
            >
            in a {historicalClassroom ? "graded" : "lecture"} section.
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
            props={{ bars: { strokeWidth: 0 }, tooltip: { hideTotal: true } }}
          />
          <p class="coverage">
            {#if historicalClassroom}Based on {current.gradedSections.toLocaleString()}
              section grade records, including non-letter outcomes. These are recorded
              outcomes, not historical enrollment snapshots; section type is unavailable.{:else}Known
              enrollment for {current.knownLectures.toLocaleString()} of {current.lectures.toLocaleString()}
              lecture sections. Labs and discussions excluded.{/if}
          </p>
          <details class="disclosure">
            <summary>Section sizes in numbers</summary>
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
        {#if !historicalClassroom}<div class="course-list">
            <h3>Big draws this term</h3>
            <p class="muted">
              Courses with the most recorded lecture enrollment.
            </p>
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
          </div>{:else}<div class="history-copy">
            <h3>A look inside past classrooms</h3>
            <p class="muted">
              We have historical section grades even where meeting schedules
              were not captured. The distribution shows how many outcomes were
              recorded per section.
            </p>
            <p class="muted">
              Explore course volumes, subjects, and rankings in the academic
              landscape above.
            </p>
          </div>{/if}
      </div>
    {:else}<p class="empty">
        Lecture enrollment isn’t available for this term. Historical grades are
        shown below where available.
      </p>{/if}
  </section>

  <section aria-labelledby="report-card">
    <div class="section-heading">
      <p class="eyebrow">03 / The grades</p>
      <h2 id="report-card">The campus report card</h2>
      <p>
        {#if gradeTerm}{termName(gradeTerm)}{gradeTerm !== term
            ? ` · latest recorded grades before ${termName(term)}`
            : " · recorded letter grades"}{:else}No recorded grades through {termName(
            term,
          )}.{/if}
      </p>
    </div>
    {#if grades?.gradeCount}
      <div class="grade-headline">
        <strong><AnimatedNumber value={grades.gpa} decimals={2} /></strong>
        <p>
          average GPA across <span
            >{grades.gradeCount.toLocaleString()} recorded letter grades.</span
          ><br /><b>{popularGrade}</b> was the most common grade.
        </p>
      </div>
      <div class="story-grid">
        <div>
          <h3>Every grade has a share</h3>
          <BarChart
            data={bars}
            x="grade"
            y="percentage"
            series={[
              {
                key: "percentage",
                label: "Percent of letter grades",
                color: "var(--accent)",
              },
            ]}
            height={280}
            props={{ bars: { strokeWidth: 0 }, tooltip: { hideTotal: true } }}
          />
          <details class="disclosure">
            <summary>Grade percentages</summary>
            <div class="grade-table">
              {#each bars as row}<div>
                  <span>{row.grade}</span><span
                    >{row.percentage.toFixed(1)}%</span
                  >
                </div>{/each}
            </div>
          </details>
        </div>
        <div>
          <h3>How the grade mix has changed</h3>
          <AreaChart
            data={gradeMix}
            x="term"
            xScale={scalePoint()}
            series={gradeLabels.map((key, i) => ({
              key,
              label: key,
              color: gradeColors[i],
            }))}
            seriesLayout="stack"
            height={280}
            yDomain={[0, 100]}
            legend={false}
            props={{
              xAxis: { tickOcclusion: true, tickSpacing: 90 },
              tooltip: {
                hideTotal: true,
                item: { format: (value: number) => value.toFixed(1) + "%" },
              },
            }}
          />
          <div class="grade-key">
            {#each gradeLabels as grade, i}<span
                ><i style:background={gradeColors[i]}></i>{grade}</span
              >{/each}
          </div>
          <details class="disclosure">
            <summary>Average GPA over time</summary>
            <LineChart
              data={trend}
              x="term"
              xScale={scalePoint()}
              yDomain={domain}
              series={[
                { key: "gpa", label: "School GPA", color: "var(--accent)" },
              ]}
              height={280}
              props={{
                xAxis: { tickOcclusion: true, tickSpacing: 90 },
                spline: { curve: curveMonotoneX, strokeWidth: 1.8 },
                points: { r: 2 },
                tooltip: {
                  hideTotal: true,
                  item: { format: (value: number) => value.toFixed(2) },
                },
              }}
            />
          </details>
          <details class="disclosure">
            <summary>Recorded GPA by term</summary>
            <div class="grade-table">
              {#each [...trend].reverse() as row}<div>
                  <span>{row.term}</span><span>{row.gpa?.toFixed(2)}</span>
                </div>{/each}
            </div>
          </details>
        </div>
      </div>
    {/if}
  </section>
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
  .grade-key {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 12px;
    margin: 12px 0;
  }
  .grade-key span {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .grade-key i {
    width: 12px;
    height: 3px;
  }
  .school-stats {
    padding: 30px 0 10px;
  }
  .intro {
    display: flex;
    justify-content: space-between;
    gap: 30px;
    align-items: flex-start;
  }
  .eyebrow {
    color: var(--accent);
    font-size: 12px;
    margin: 0 0 18px;
    letter-spacing: 0.05em;
  }
  h1 {
    font-size: clamp(44px, 6vw, 80px);
    line-height: 1.02;
    letter-spacing: -0.06em;
    font-weight: 550;
    margin: 0 0 24px;
  }
  .lede {
    max-width: 510px;
    font-size: 17px;
    line-height: 1.6;
    color: var(--muted);
  }
  .term-picker {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-top: 4px;
  }
  .term-picker button {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border: 1px solid var(--border);
    border-radius: 5px;
    background: var(--surface);
    color: var(--text);
    cursor: pointer;
  }
  .term-picker button:disabled {
    opacity: 0.3;
    cursor: default;
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
  section {
    margin-top: 90px;
  }
  .section-heading {
    margin-bottom: 35px;
  }
  .section-heading .eyebrow {
    margin-bottom: 10px;
  }
  h2 {
    font-size: clamp(28px, 3.5vw, 42px);
    letter-spacing: -0.045em;
    font-weight: 500;
    margin: 0 0 12px;
  }
  .section-heading > p:last-child,
  .coverage {
    color: var(--muted);
  }
  h3 {
    font-size: 17px;
    font-weight: 500;
    margin: 0 0 20px;
  }
  .story-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: clamp(28px, 5vw, 70px);
    align-items: start;
  }
  .story-grid > div {
    min-width: 0;
  }
  .observation {
    font-size: 21px;
    line-height: 1.45;
    letter-spacing: -0.02em;
    max-width: 430px;
    margin: 0 0 26px;
  }
  .observation strong {
    font-weight: 500;
    color: var(--accent);
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
  .coverage {
    font-size: 12px;
    line-height: 1.6;
  }
  .course-list > p {
    font-size: 13px;
    margin-top: -10px;
    margin-bottom: 20px;
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
  .grade-headline {
    display: flex;
    gap: 24px;
    align-items: center;
    margin-bottom: 35px;
  }
  .grade-headline > strong {
    font-size: 72px;
    font-weight: 450;
    letter-spacing: -0.06em;
    color: var(--accent);
  }
  .grade-headline p {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.7;
  }
  .grade-headline b {
    color: var(--text);
    font-weight: 500;
  }
  .disclosure {
    margin-top: 25px;
    font-size: 13px;
  }
  summary {
    cursor: pointer;
    color: var(--muted);
  }
  .building-list,
  .grade-table {
    margin-top: 16px;
    max-height: 320px;
    overflow: auto;
  }
  .building-list > div,
  .grade-table > div {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    padding: 8px 0;
  }
  small {
    color: var(--muted);
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
  @media (max-width: 760px) {
    .intro {
      flex-direction: column;
      gap: 15px;
    }
    .story-grid {
      grid-template-columns: 1fr;
      gap: 35px;
    }
    section {
      margin-top: 65px;
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
    }
    .grade-headline {
      gap: 20px;
    }
    .grade-headline > strong {
      font-size: 60px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .cell {
      transition: none;
    }
  }
</style>
