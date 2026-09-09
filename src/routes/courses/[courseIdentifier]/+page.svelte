<script lang="ts">
  import { onMount, setContext } from "svelte";
  import {
    ArrowUpRight,
    ChevronLeft,
    ChevronRight,
    BookOpen,
    GitBranch,
    CalendarDays,
    Users,
    ChartColumn,
    Layers,
    Info,
  } from "@lucide/svelte";
  import { Tooltip } from "bits-ui";
  import { citationContext, citationKey, citationNumbers } from "$lib/citations";
  import { courseFitObservations } from "$lib/course-fit";
  import type { Citation } from "$lib/types";
  import Select from "$lib/components/Select.svelte";
  import Panel from "$lib/components/Panel.svelte";
  import Claims from "$lib/components/Claims.svelte";
  import RotatingClaims from "$lib/components/RotatingClaims.svelte";
  import Evidence from "$lib/components/Evidence.svelte";
  import InstructorStats from "$lib/components/InstructorStats.svelte";
  import CourseContext from "$lib/components/CourseContext.svelte";
  import GradeSnapshot from "$lib/components/GradeSnapshot.svelte";
  import Grades from "$lib/components/Grades.svelte";
  import RequirementGraph from "$lib/components/RequirementGraph.svelte";
  import RequirementText from "$lib/components/RequirementText.svelte";
  import CourseCalendar from "$lib/components/CourseCalendar.svelte";
  import { credits,  termName, courseTitle, courseUrl } from "$lib/format";
  let { data } = $props();
  let c = $derived(data.course);
  let comparisonScope = $state("school");
  let experienceInfoOpen = $state(false);
  let scope = $derived(c.subjects.includes(comparisonScope) ? comparisonScope : "school");
  let termSelection = $state<string | null>(null);
  let projectedTerm = $derived(c.grades.some((row: any) => row.term_id === c.semester && ["a", "ab", "b", "bc", "c", "d", "f"].some((key) => row[key] > 0)) ? "" : c.semester);
  let gradeTerms = $derived([...new Set<string>([c.semester, ...c.grades.map((row: any) => row.term_id), ...c.sections.map((row: any) => row.term_id)].filter(Boolean))].sort().reverse());
  let selectedGradeTerm = $derived(termSelection ?? gradeTerms[0] ?? c.semester);
  let gradeTermIndex = $derived(gradeTerms.indexOf(selectedGradeTerm));
  function stepTerm(direction: number) {
    const index = gradeTermIndex + direction;
    if (index >= 0 && index < gradeTerms.length) termSelection = gradeTerms[index];
  }
  let termLabel = $derived(selectedGradeTerm ? termName(selectedGradeTerm) : "All recorded terms");
  let snapshotAvailable = $derived(!selectedGradeTerm || selectedGradeTerm === c.semester);
  let selectedSections = $derived(c.sections.filter((section: any) => !selectedGradeTerm || section.term_id === selectedGradeTerm));
  let selectedOfferings = $derived(c.offerings.filter((offering: any) => !selectedGradeTerm || offering.term_id === selectedGradeTerm));
  let professors = $derived.by(() => {
    const roster = new Map<string, any>();
    if (snapshotAvailable) for (const instructor of c.instructors) roster.set(instructor.instructor_uid, instructor);
    for (const instructor of c.grade_instructors || []) {
      const history = data.instructorTrends.find((row) => row.uid === instructor.instructor_uid);
      if ((!selectedGradeTerm || history?.terms.some((row) => row.term === selectedGradeTerm)) && !roster.has(instructor.instructor_uid)) roster.set(instructor.instructor_uid, instructor);
    }
    return [...roster.values()].map((instructor) => {
      const terms = data.instructorTrends.find((row) => row.uid === instructor.instructor_uid)?.terms.filter((row) => !selectedGradeTerm || row.term === selectedGradeTerm) || [];
      const graded = terms.reduce((sum, row) => sum + row.count, 0);
      return { ...instructor, name: instructor.name || "Unknown instructor", grade_statistics: graded ? {
        graded, gpa: terms.reduce((sum, row) => sum + row.gpa * row.count, 0) / graded,
        sections: terms.reduce((sum, row) => sum + (row.sections || 0), 0),
      } : null };
    }).sort((a, b) => (b.ratings?.bayesian_quality ?? -1) - (a.ratings?.bayesian_quality ?? -1) || a.name.localeCompare(b.name));
  });
  let headerProfessors = $derived([... (selectedGradeTerm ? professors : c.instructors)].sort((a, b) => (b.ratings?.bayesian_quality ?? -1) - (a.ratings?.bayesian_quality ?? -1) || (a.name || "").localeCompare(b.name || "")));
  let benchmark = $derived(selectedGradeTerm ? data.context?.benchmarks.terms[selectedGradeTerm]?.[scope] : data.context?.benchmarks.all[scope]);
  $effect(() => { c.course_uid; termSelection = null; });
  let allTimeSummary = $derived(c.student_summary);
  let observationTerm = $derived(c.sections.map((section: any) => section.term_id).filter(Boolean).sort().at(-1));
  let overviewClaims = $derived([
    ...(allTimeSummary.difficulty_workload || []), ...(allTimeSummary.quick_take || []), ...(allTimeSummary.student_experience || []),
    ...courseFitObservations({
      gpa: (data.context?.all?.count ?? 0) >= 30 ? data.context?.all?.gpa : null,
      reference: data.context?.benchmarks.all[scope]?.gpa,
      group: scope === "school" ? "UW–Madison" : scope,
      sections: c.sections.filter((section: any) => section.term_id === observationTerm),
    }).map(({ text, kind }) => ({ text, source: kind === "grades" ? "Recorded grades · all terms" : `Section enrollment · ${termName(observationTerm)} snapshot`, href: kind === "grades" ? "#grades" : "#schedule" })),
  ]);
  let summary = $derived(!selectedGradeTerm || selectedGradeTerm === c.student_summary?.term_id ? c.student_summary : {});
  let sourceNumbers = $derived(citationNumbers(allTimeSummary));
  setContext(citationContext, (citation: Citation) => sourceNumbers.get(citationKey(citation)));
  let active = $state("overview");
  let navigationHeight = $state(43);
  let introduction = $derived(
    (c.llm_summary || c.description || "")
      .replace(`${c.course_id} ${c.title} `, "")
      .replace(/^./, (letter: string) => letter.toUpperCase()),
  );
  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries)
          if (entry.isIntersecting) active = entry.target.id;
      },
      { rootMargin: "-10% 0px -65% 0px" },
    );
    for (const link of links) {
      const section = document.getElementById(link.id);
      if (section) observer.observe(section);
    }
    return () => observer.disconnect();
  });
  const links = [
    { id: "overview", label: "overview", icon: BookOpen },
    { id: "requirements", label: "prerequisites", icon: GitBranch },
    { id: "professors", label: "professors", icon: Users },
    { id: "schedule", label: "calendar", icon: CalendarDays },
    { id: "experience", label: "student experience", icon: BookOpen },
    { id: "grades", label: "grades", icon: ChartColumn },
    { id: "evidence", label: "sources", icon: Layers },
  ];</script>

<svelte:head
  ><title>{c.course_id} · {c.title} · UW Courses</title><meta
    name="description"
    content={c.llm_summary || c.description?.slice(0, 160)}
  /><link rel="canonical" href={courseUrl(c.course_id)} /></svelte:head
>
<div class="course-page" style={`--course-navigation-height: ${navigationHeight}px`}>
<div class="course-heading">
  <div class="row between">
    <div class="breadcrumbs mono">
      <a href="/search">courses</a><span>/</span><span>{c.course_id}</span>
    </div>
    <span class="mono muted">{selectedGradeTerm ? termLabel : termName(c.semester)}</span>
  </div>
  <div class="course-identity">
    <div>
      <h1 title={c.title}>{courseTitle(c.title)}</h1>
      <p class="course-description">{introduction}</p>
      <div class="row course-meta">
        <span class:available={selectedOfferings.length}
          ><i></i>{selectedOfferings.length ? "offering recorded" : "no offering record for this term"}</span
        ><span>{credits(c.credits_min, c.credits_max)}</span>
      </div>
    </div>
    <div class="current-teachers">
      <span class="teacher-label">{selectedGradeTerm ? `Recorded instructors · ${termLabel}` : `Teaching · ${termName(c.semester)}`}</span>
      {#each headerProfessors.slice(0, 3) as instructor}<a
          href={instructor.instructor_url}
          ><span>{instructor.name}</span
          >{#if instructor.ratings?.bayesian_quality != null}<span
              class="teacher-rating"
              aria-label={`Adjusted rating ${instructor.ratings.bayesian_quality.toFixed(1)} out of 5, from ${instructor.ratings.review_count} captured reviews`}
              >{instructor.ratings.bayesian_quality.toFixed(1)}<small>/5</small></span
            >{/if}<ArrowUpRight size={15} /></a
        >{:else}<span class="muted">No instructors listed</span>{/each}
      {#if headerProfessors.length > 3}<a class="more-teachers" href="#professors">+{headerProfessors.length - 3} more <ArrowUpRight size={15} /></a>{/if}
    </div>
  </div>
</div>
<div class="course-navigation" bind:offsetHeight={navigationHeight}>
  <nav class="course-jumps" aria-label="Course sections">
    {#each links as link}<a
        href={"#" + link.id}
        aria-current={active === link.id ? "location" : undefined}
        ><link.icon size={14} strokeWidth={1.5} />{link.label}</a
      >{/each}
  </nav>
  <div class="navigation-filters">
    {#if data.context}
      <div class="navigation-filter">
        <Select label="Comparison group" value={scope} onChange={(value) => comparisonScope = value} options={[{ value: "school", label: "School · UW–Madison" }, ...c.subjects.map((subject: string) => ({ value: subject, label: `Department · ${subject}` }))]} />
      </div>
    {/if}
    <div class="navigation-filter term-picker" role="group" aria-label="Grade term">
      <button class="term-step" aria-label={selectedGradeTerm ? "Previous term" : "Latest term"} disabled={!gradeTerms.length || gradeTermIndex >= gradeTerms.length - 1} onclick={() => stepTerm(1)}><ChevronLeft size={14} /></button>
      <Select label="Term" value={selectedGradeTerm} onChange={(value) => termSelection = value} options={[{ value: "", label: "All recorded terms" }, ...gradeTerms.map((term) => ({ value: term, label: termName(term) + (term === projectedTerm && data.projection?.interval ? " · Projected" : "") }))]} />
      <button class="term-step" aria-label="Next term" disabled={gradeTermIndex <= 0} onclick={() => stepTerm(-1)}><ChevronRight size={14} /></button>
    </div>
  </div>
</div>
<section class="course-overview" id="overview" aria-label="Course overview">
  <div class="overview-take">
    {#if overviewClaims.length}
      {#key c.course_uid}<RotatingClaims
        claims={overviewClaims}
        reviewFiles={c.evidence.reviews}
      />{/key}
    {:else}<h2>Summary</h2><p class="muted">No student feedback recorded yet.</p>{/if}
  </div>
  <GradeSnapshot grades={c.grades} benchmark={data.context?.benchmarks.all[scope]} group={scope === "school" ? "UW–Madison" : scope} />
</section>
<div class="course-workspace">
  <aside class="course-facts" aria-label="Course details">
    <Panel title="Course details">
      {#if !snapshotAvailable}<p class="muted">Catalog details below are from {termName(c.semester)}; no catalog snapshot for {termLabel}.</p>{/if}
      <div class="fact-pair">
        <span>Credits</span><strong
          >{credits(c.credits_min, c.credits_max)}</strong
        >
      </div>
      <div class="fact-pair">
        <span>Typically offered</span><strong
          >{[
            ...new Set(
              selectedOfferings.map((o: any) => o.typically_offered).filter(Boolean),
            ),
          ].join(" · ") || "Not recorded"}</strong
        >
      </div>
      <div class="fact-pair">
        <span>Subjects</span>
        <div class="row">
          {#each c.subjects as subject}<a
              href={"/departments/" + encodeURIComponent(subject)}>{subject}</a
            >{/each}
        </div>
      </div>
      <a class="small-link" href="#requirements"
        >View prerequisites <ArrowUpRight size={14} /></a
      >
      <details>
        <summary>Catalog description</summary>
        <p>{c.description}</p>
      </details>
      <details>
        <summary>Assumed background</summary>
        <ul>
          {#each c.llm_assumed_background as item}<li>{item}</li>{/each}
        </ul>
      </details>
    </Panel>
  </aside>
  <div class="course-content">
    <Panel title="Prerequisites" id="requirements">
      <a class="small-link" href={`/explorer/${encodeURIComponent(c.subjects[0])}?course=${encodeURIComponent(c.course_id)}`}>Explore connected courses on the map →</a>
      {#if snapshotAvailable}
      <p class="requirements-source">
        {c.requirements_text || "No prerequisites listed."}
      </p>
      <RequirementGraph ast={c.requirements} course={c.course_id} following={data.following} />
      {#if c.requirements.status !== "valid"}<p class="muted mono">
          Best-effort interpretation · check the original requirements above.
        </p>{/if}
      <details>
        <summary>Prerequisite text tree</summary><RequirementText
          ast={c.requirements}
        />
      </details>
      {:else}<p class="muted">No prerequisite snapshot for {termLabel}. The available prerequisite tree is from {termName(c.semester)}.</p>{/if}
    </Panel>
    <Panel title="Professors" id="professors" label={termLabel}>
      <div class="professor-grid">
        {#each professors as i}{@const feedback =
            summary.current_instructors?.find(
              (r: any) => r.instructor_uid === i.instructor_uid,
            )}
          <article class="professor-tile">
            <div class="professor-heading">
              <span class="avatar" aria-hidden="true"
                >{i.name
                  .split(" ")
                  .map((s: string) => s[0])
                  .slice(0, 2)
                  .join("")}</span
              >
              <h3>
                <a href={i.instructor_url}
                  >{i.name}<ArrowUpRight size={13} /></a
                >
              </h3>
            </div>
            <div>
              <InstructorStats
                ratings={i.ratings}
                grades={i.grade_statistics}
                courseUid={c.course_uid}
                {benchmark}
                group={scope === "school" ? "UW–Madison" : scope}
                term={selectedGradeTerm}
              />
              {#if feedback?.summary?.length}<Claims
                  claims={feedback.summary}
                  reviewFiles={c.evidence.reviews}
                />{:else}<p class="muted">
                  No course-specific feedback yet.
                </p>{/if}
            </div>
          </article>{:else}<p class="muted">
            No instructors recorded for this selection.
          </p>{/each}
      </div>
      <details>
        <summary>Historical instructors & teaching patterns</summary>
        <div class="stack">
          <Claims
            claims={summary.historical_context || []}
            reviewFiles={c.evidence.reviews}
          /><Claims
            claims={summary.teaching_history || []}
            reviewFiles={c.evidence.reviews}
          />
          <p class="muted">
            Recorded history may be incomplete and does not establish a future
            schedule.
          </p>
        </div>
      </details>
    </Panel>
    <Panel
      title="Calendar & sections"
      id="schedule"
      label={selectedGradeTerm ? termLabel : termName(c.semester)}
    >
      {#if snapshotAvailable}<CourseCalendar
        files={c.evidence.meetings || []}
        observedAt={c.observed_at}
      />
      {:else}<p class="muted">No calendar captured for {termLabel}.</p>{/if}
      <div class="table-scroll">
        <table>
          <thead
            ><tr
              ><th>Section</th><th>Mode</th><th>Enrolled / capacity</th><th
                >Waitlist</th
              ></tr
            ></thead
          ><tbody
            >{#each selectedSections as s}<tr
                ><td
                  ><span class="mono">{s.section_type} {s.section_number}</span
                  ></td
                ><td>{s.instruction_mode || "—"}</td><td
                  >{s.enrolled ?? "—"} / {s.capacity ?? "—"}</td
                ><td>{s.waitlisted ?? "—"}</td></tr
              >{/each}</tbody
          >
        </table>
      </div>
      {#if selectedSections.length}<p class="muted mono">Enrollment at scan time.</p>{/if}
      {#if snapshotAvailable}<Evidence
        title="Meeting source records"
        files={c.evidence.meetings || []}
      />{/if}
    </Panel>
    <Panel
      title="Student experience"
      id="experience"
    >
      {#snippet tools()}
        <Tooltip.Provider delayDuration={200}><Tooltip.Root bind:open={experienceInfoOpen} disableCloseOnTriggerClick>
          <Tooltip.Trigger class="experience-info" aria-label="About student experience" onclick={() => experienceInfoOpen = true}><Info size={16} /></Tooltip.Trigger>
          <Tooltip.Portal><Tooltip.Content class="experience-info-content" role="tooltip" sideOffset={6}>
            {snapshotAvailable ? `AI-generated from captured student reviews · ${termName(c.student_summary?.term_id || c.semester)}. Open citations to read the original comments.` : `No student-experience summary for ${termLabel}. Reviews are not reliably assigned to teaching terms.`}
          </Tooltip.Content></Tooltip.Portal>
        </Tooltip.Root></Tooltip.Provider>
      {/snippet}
      {#if snapshotAvailable}<div class="experience-grid">
        <div>
          <h3 class="tile-label">the class</h3>
          <Claims
            claims={summary.quick_take || []}
            reviewFiles={c.evidence.reviews}
          />{#if !summary.quick_take?.length}<p>{c.description}</p>{/if}
        </div>
        <div>
          <h3 class="tile-label">difficulty & workload</h3>
          <Claims
            claims={summary.difficulty_workload || []}
            reviewFiles={c.evidence.reviews}
          />{#if !summary.difficulty_workload?.length}<p class="muted">
              No workload feedback recorded.
            </p>{/if}
        </div>
      </div>
      {#if summary.student_experience?.length}<div class="experience-notes">
          <Claims
            claims={summary.student_experience}
            reviewFiles={c.evidence.reviews}
          />
        </div>{/if}
    {#if c.llm_topics?.length || c.llm_skills?.length}
      <section class="course-topics" id="topics" aria-label="AI-generated topics and skills">
        <div class="course-tag-groups">
          {#each [{ label: "Topics", values: c.llm_topics }, { label: "Skills", values: c.llm_skills }] as group}
            {#if group.values?.length}
              <div>
                <h3 class="tag-label">{group.label}</h3>
                <ul class="course-tags" aria-label={group.label}>
                  {#each group.values as tag}<li>{tag}</li>{/each}
                </ul>
              </div>
            {/if}
          {/each}
        </div>
      </section>
    {/if}
    {:else}<p class="muted">No student-experience summary for {termLabel}. Reviews are not reliably assigned to teaching terms.</p>{/if}
    </Panel>
    <Panel title="Grades" id="grades">
      <Grades
        grades={c.grades}
        projection={data.projection}
        {projectedTerm}
        instructorTrends={data.instructorTrends}
        selectedTerm={selectedGradeTerm}
        showTermSelect={false}
        benchmarks={data.context?.benchmarks}
        {scope}
        uid={c.course_uid}
        revision={c.revision}
        instructors={c.grade_instructors || c.instructors}
      />
      {#if c.grade_conflicts?.length}<details>
          <summary>Conflicting source distributions</summary>
          <p class="muted">Excluded from calculated GPA.</p>
          <pre>{JSON.stringify(c.grade_conflicts, null, 2)}</pre>
        </details>{/if}
    </Panel>
    {#if data.context}<CourseContext context={data.context} subjects={c.subjects} {scope} onScopeChange={(value) => comparisonScope = value} term={selectedGradeTerm} />{/if}
    <Panel title="Sources & history" id="evidence">
      <details>
        <summary>Selected offering source records</summary>
        <pre>{JSON.stringify(selectedOfferings, null, 2)}</pre>
      </details>
      <Evidence
        title="Catalog observation history"
        files={c.evidence.history || []}
        description="These are observations at scan time, not inferred catalog validity periods."
      /><Evidence
        title="Student reviews"
        files={c.evidence.reviews || []}
      /><Evidence
        title="LLM outputs across runs"
        files={c.evidence.results || []}
      /><Evidence
        title="Full model traces"
        files={c.evidence.traces || []}
        description="Includes the recorded model configuration, reasoning and tool conversation where available."
      />{#if c.catalog_variants?.length}<details>
          <summary>Cross-listed catalog records</summary>
          <pre>{JSON.stringify(c.catalog_variants, null, 2)}</pre>
        </details>{/if}
      <details>
        <summary>Model & dataset provenance</summary>
        <pre>{JSON.stringify(
            {
              model: c.llm_model,
              model_revision: c.llm_model_revision,
              task_version: c.llm_task_version,
              output_id: c.llm_output_id,
              requirements_status: c.llm_requirements_status,
              dataset_revision: c.revision,
              observed_at: c.observed_at,
            },
            null,
            2,
          )}</pre>
      </details>
      <a
        class="mono"
        href={`https://huggingface.co/datasets/${data.status.repository}/tree/${c.revision}`}
        >Download the original dataset ↗</a
      >
    </Panel>
  </div>
</div>

</div>

<style>
  :global(.experience-info) { display: grid; place-items: center; padding: 4px; border: 0; background: transparent; color: var(--muted); cursor: help; }
  :global(.experience-info-content) { z-index: 100; max-width: 270px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); color: var(--muted); font-size: 12px; line-height: 1.6; box-shadow: 0 5px 20px #0001; }
  .course-page {
    width: 100%;
  }
  .course-topics { margin-top: 28px; }
  .course-navigation { display: flex; align-items: center; gap: 20px; position: sticky; top: 0; z-index: 20; background: var(--bg); border-bottom: 1px solid var(--border); padding: 6px 0; }
  .course-navigation .course-jumps { position: static; flex: 1; min-width: 0; border: 0; margin: 0; padding: 0; }
  .course-navigation .course-jumps a { height: 30px; box-sizing: border-box; font-size: 12px; padding: 0 8px; gap: 5px; }
  .navigation-filter :global(.course-select-trigger) { height: 30px; box-sizing: border-box; padding-block: 0; }
  .navigation-filter.term-picker { grid-template-columns: 28px minmax(0, 1fr) 28px; gap: 0; height: 30px; box-sizing: border-box; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); }
  .term-picker :global(.course-select-trigger) { height: 28px; border: 0; border-inline: 1px solid var(--border); border-radius: 0; background: transparent; }
  .term-picker .term-step { width: 28px; height: 28px; border-radius: 0; }
  .term-picker .term-step:first-child { border-radius: 4px 0 0 4px; }
  .term-picker .term-step:last-child { border-radius: 0 4px 4px 0; }
  .term-step { display: grid; place-items: center; width: 26px; height: 30px; padding: 0; border: 0; border-radius: 4px; background: transparent; color: var(--muted); cursor: pointer; }
  .term-step:hover:not(:disabled) { background: var(--border); color: var(--text); }
  .term-step:disabled { opacity: 0.3; cursor: default; }
  .term-step:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .navigation-filters { display: flex; gap: 10px; flex-shrink: 0; }
  .navigation-filter { display: grid; gap: 2px; min-width: 0; }
  @media (max-width: 1000px) {
    .course-navigation { flex-wrap: wrap; gap: 10px; }
    .course-navigation .course-jumps { flex-basis: 100%; }
    .navigation-filters { width: 100%; }
    .navigation-filter { flex: 1; }
    .course-overview, .course-workspace :global(section) { scroll-margin-top: 145px; }
  }

  .course-tag-groups {
    display: grid;
    gap: 14px;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.65;
  }
  .tag-label {
    font-size: inherit;
    font-weight: 500;
    margin: 0 0 4px;
  }
  .course-tags {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .course-tags li {
    display: inline;
    overflow-wrap: anywhere;
  }
  .course-tags li + li::before {
    content: " · ";
    white-space: pre-wrap;
  }
</style>
