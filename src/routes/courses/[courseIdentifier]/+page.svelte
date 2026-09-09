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
  } from "@lucide/svelte";
  import { citationContext, citationKey, citationNumbers } from "$lib/citations";
  import { courseFitObservations } from "$lib/course-fit";
  import type { Citation } from "$lib/types";
  import Select from "$lib/components/Select.svelte";
  import AIDisclaimer from "$lib/components/AIDisclaimer.svelte";
  import Badges from "$lib/components/Badges.svelte";
  import { courseBadges, instructorBadges } from "$lib/badges";
  import Panel from "$lib/components/Panel.svelte";
  import Claims from "$lib/components/Claims.svelte";
  import RotatingClaims from "$lib/components/RotatingClaims.svelte";
  import Evidence from "$lib/components/Evidence.svelte";
  import InstructorStats from "$lib/components/InstructorStats.svelte";
  import CourseContext from "$lib/components/CourseContext.svelte";
  import GradeSnapshot from "$lib/components/GradeSnapshot.svelte";
  import Grades from "$lib/components/Grades.svelte";
  import { departmentName } from "$lib/departments";
  import { requirementText } from "$lib/requirements";
  import RequirementGraph from "$lib/components/RequirementGraph.svelte";
  import RequirementText from "$lib/components/RequirementText.svelte";
  import CourseCalendar from "$lib/components/CourseCalendar.svelte";
  import { credits,  termName, courseTitle, courseUrl } from "$lib/format";
  let { data } = $props();
  let c = $derived(data.course);
  let comparisonScope = $state("school");
  let scope = $derived(c.subjects.includes(comparisonScope) ? comparisonScope : "school");
  let termSelection = $state<string | null>(null);
  let projectedTerm = $derived(c.grades.some((row: any) => row.term_id === c.semester && ["a", "ab", "b", "bc", "c", "d", "f"].some((key) => row[key] > 0)) ? "" : c.semester);
  let gradeTerms = $derived([...new Set<string>([c.semester, ...c.grades.map((row: any) => row.term_id), ...c.sections.map((row: any) => row.term_id)].filter(Boolean))].sort().reverse());
  let selectedGradeTerm = $derived(termSelection ?? gradeTerms[0] ?? c.semester);
  let badgeInstructors = $derived([
    ...c.instructors.map((i: any) => ({ ...i, terms: [{ term: c.semester }] })),
    ...(c.grade_instructors || []).map((i: any) => ({ ...i, terms: data.instructorTrends.find((row) => row.uid === i.instructor_uid)?.terms || [] })),
  ]);
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
  let stickyTitle = $state(false);
  let navigationHeight = $state(43);
  let sectionNav: HTMLElement;
  let indicator = $state({ left: 0, width: 0 });
  let introduction = $derived(
    (c.llm_summary || c.description || "")
      .replace(`${c.course_id} ${c.title} `, "")
      .replace(/^./, (letter: string) => letter.toUpperCase()),
  );
  onMount(() => {
    let frame = 0;
    let stopped = false;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    function update() {
      frame = 0;
      stickyTitle = (document.querySelector(".course-heading")?.getBoundingClientRect().bottom ?? 1) <= 0;
      const sections = links.map(link => document.getElementById(link.id)).filter((el): el is HTMLElement => !!el);
      const threshold = navigationHeight + 64;
      let next = sections[0]?.id || "overview";
      for (const section of sections) if (section.getBoundingClientRect().top <= threshold) next = section.id;
      if (window.scrollY > 0 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) next = sections.at(-1)?.id || next;
      const changed = next !== active;
      active = next;
      const link = sectionNav.querySelector<HTMLAnchorElement>(`a[href="#${next}"]`);
      if (!link) return;
      indicator = { left: link.offsetLeft, width: link.offsetWidth };
      // Scroll only the horizontal navigation, never the document.
      if (changed && (link.offsetLeft < sectionNav.scrollLeft || link.offsetLeft + link.offsetWidth > sectionNav.scrollLeft + sectionNav.clientWidth)) {
        sectionNav.scrollTo({ left: link.offsetLeft - (sectionNav.clientWidth - link.offsetWidth) / 2, behavior: motion.matches ? "instant" : "smooth" });
      }
    }
    function schedule() { if (!frame && !stopped) frame = requestAnimationFrame(update); }
    window.addEventListener("scroll", schedule, { passive: true });
    const resize = new ResizeObserver(schedule);
    resize.observe(sectionNav);
    resize.observe(sectionNav.closest(".course-navigation")!);
    resize.observe(sectionNav.firstElementChild!);
    resize.observe(document.querySelector(".course-workspace")!);
    document.fonts.ready.then(schedule);
    schedule();
    return () => { stopped = true; cancelAnimationFrame(frame); resize.disconnect(); window.removeEventListener("scroll", schedule); };
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

<div class="course-page" style={`--course-navigation-height: ${navigationHeight}px`}>
<div class="course-heading">
  <div class="row between">
    <nav class="breadcrumbs mono" aria-label="Breadcrumb">
      <a href="/departments">departments</a><span>/</span>
      {#if c.subjects.length}<a href={`/departments/${encodeURIComponent(c.subjects[0])}`}>{departmentName(c.subjects[0])}</a><span>/</span>{/if}<span>{c.course_id}</span>
    </nav>
    <span class="mono muted">{selectedGradeTerm ? termLabel : termName(c.semester)}</span>
  </div>
  <div class="course-identity">
    <div>
      <h1 title={c.title}>{courseTitle(c.title)}</h1>
      <Badges badges={courseBadges({ course: c, context: data.context, term: selectedGradeTerm, scope, instructors: badgeInstructors })} limit={3} />
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
  {#if stickyTitle}<div class="sticky-course-title" aria-hidden="true"><span class="sticky-course-code" title={c.course_id}>{c.course_id}</span><span class="sticky-course-name" title={courseTitle(c.title)}>{courseTitle(c.title)}</span></div>{/if}
  <div class="navigation-row">
  <nav bind:this={sectionNav} class="course-jumps" class:has-indicator={indicator.width > 0} aria-label="Course sections">
    <div class="section-links">
    {#each links as link}<a
        href={"#" + link.id}
        aria-current={active === link.id ? "location" : undefined}
        ><link.icon size={14} strokeWidth={1.5} />{link.label}</a
      >{/each}
      <span class="section-indicator" aria-hidden="true" style:width={`${indicator.width}px`} style:transform={`translateX(${indicator.left}px)`}></span>
    </div>
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
</div>
<section class="course-overview" id="overview" aria-label="Course overview">
  <div class="overview-take">
    {#if overviewClaims.length}
      {#key c.course_uid}<RotatingClaims
        claims={overviewClaims}
        model={c.llm_model}
        revision={c.llm_model_revision}
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
        <div class="subject-links">
          {#each c.subjects as subject, index}{index > 0 ? ", " : ""}<a
              href={"/departments/" + encodeURIComponent(subject)}>{departmentName(subject)}</a
            >{/each}
        </div>
      </div>
      <div class="course-reading">
        <article class="catalog-description">
          <h3>About this course</h3>
          <p>{c.description || "No catalog description available."}</p>
        </article>
        {#if c.llm_assumed_background.length}
          <aside class="helpful-background" aria-label="Helpful background">
            <h3>Helpful background <AIDisclaimer model={c.llm_model} revision={c.llm_model_revision} label="About AI suggestions" description="Suggested background is not an official prerequisite." /></h3>
            <ul>{#each c.llm_assumed_background as item}<li>{item}</li>{/each}</ul>
          </aside>
        {/if}
      </div>
    </Panel>
  </aside>
  <div class="course-content">
    <Panel title="Prerequisites" id="requirements">
      {#snippet tools()}<a class="prerequisite-map-link" href={`/explorer/${encodeURIComponent(c.subjects[0])}?course=${encodeURIComponent(c.course_id)}`}>Course map <ArrowUpRight size={15} /></a>{/snippet}
      {#if snapshotAvailable}
      <p class="requirements-source">
        {requirementText(c.requirements_text || "No prerequisites listed.")}
      </p>
      <RequirementGraph ast={c.requirements} course={c.course_id} following={data.following} />
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
            <div>
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
            <Badges badges={instructorBadges(i.ratings)} />
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
      {#if selectedSections.length || snapshotAvailable}<p class="section-note">
        {#if snapshotAvailable}Times are Central. Select a meeting for details; export includes recorded dates for the selected sections. {/if}
        {#if selectedSections.length}Enrollment reflects scan time.{/if}
      </p>{/if}
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
        <AIDisclaimer model={c.llm_model} revision={c.llm_model_revision} label="About student experience" description={snapshotAvailable ? `Captured student reviews · ${termName(c.student_summary?.term_id || c.semester)}. Citations open the original comments.` : `No student-experience summary for ${termLabel}. Reviews are not reliably assigned to teaching terms.`} />
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
  .course-page {
    width: 100%;
  }
  .course-topics { margin-top: 28px; }
  .course-navigation { position: sticky; top: 0; z-index: 20; background: var(--bg); border-bottom: 1px solid var(--border); }
  .navigation-row { display: flex; align-items: center; gap: 20px; padding: 6px 0; }
  .sticky-course-title { display: flex; align-items: baseline; gap: 12px; min-width: 0; padding: 10px 8px 4px; }
  .sticky-course-code { flex-shrink: 0; max-width: 45%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); font-size: 12px; }
  .sticky-course-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 15px; font-weight: 500; }
  .course-overview, .course-workspace :global(section) { scroll-margin-top: calc(var(--course-navigation-height, 43px) + 32px); }
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
  .section-links { position: relative; display: flex; flex: 0 0 auto; width: max-content; gap: 5px; }
  .section-indicator { position: absolute; left: 0; bottom: 0; height: 2px; background: var(--accent); border-radius: 2px; pointer-events: none; transition: transform var(--motion-travel) var(--motion-ease), width var(--motion-travel) var(--motion-ease); }
  .has-indicator a[aria-current="location"] { box-shadow: none; }
  @media (prefers-reduced-motion: reduce) { .section-indicator { transition: none; } }
  .navigation-filters { display: flex; gap: 10px; flex-shrink: 0; }
  .navigation-filter { display: grid; gap: 2px; min-width: 0; }
  @media (max-width: 1000px) {
    .navigation-row { flex-wrap: wrap; gap: 10px; }
    .course-navigation .course-jumps { flex-basis: 100%; }
    .navigation-filters { width: 100%; }
    .navigation-filter { flex: 1; }
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
