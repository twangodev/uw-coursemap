<script lang="ts">
  import { onMount } from "svelte";
  import {
    ArrowUpRight,
    BookOpen,
    GitBranch,
    CalendarDays,
    Users,
    ChartColumn,
    Layers,
  } from "@lucide/svelte";
  import Panel from "$lib/components/Panel.svelte";
  import Claims from "$lib/components/Claims.svelte";
  import Evidence from "$lib/components/Evidence.svelte";
  import GradeSnapshot from "$lib/components/GradeSnapshot.svelte";
  import Grades from "$lib/components/Grades.svelte";
  import RequirementText from "$lib/components/RequirementText.svelte";
  import CourseCalendar from "$lib/components/CourseCalendar.svelte";
  import { credits, instructorUrl, termName, courseTitle } from "$lib/format";
  let { data } = $props();
  let c = $derived(data.course);
  let summary = $derived(c.student_summary);
  let Graph = $state<any>(null);
  let graphError = $state("");
  let active = $state("overview");
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
  onMount(() => {
    import("$lib/components/RequirementGraph.svelte")
      .then((m) => (Graph = m.default))
      .catch(
        () =>
          (graphError = "Graph unavailable. The complete text tree is below."),
      );
  });
  const links = [
    { id: "overview", label: "overview", icon: BookOpen },
    { id: "grades", label: "grades", icon: ChartColumn },
    { id: "experience", label: "student experience", icon: BookOpen },
    { id: "professors", label: "professors", icon: Users },
    { id: "requirements", label: "prerequisites", icon: GitBranch },
    { id: "schedule", label: "calendar", icon: CalendarDays },
    { id: "evidence", label: "sources", icon: Layers },
  ];
</script>

<svelte:head
  ><title>{c.course_id} · {c.title} · UW Courses</title><meta
    name="description"
    content={c.llm_summary || c.description?.slice(0, 160)}
  /></svelte:head
>
<div class="course-heading">
  <div class="row between">
    <div class="breadcrumbs mono">
      <a href="/search">courses</a><span>/</span><span>{c.course_id}</span>
    </div>
    <span class="mono muted">{termName(c.semester)}</span>
  </div>
  <div class="course-identity">
    <div>
      <h1 title={c.title}>{courseTitle(c.title)}</h1>
      <p class="course-description">{introduction}</p>
    </div>
    <div class="current-teachers">
      <span class="teacher-label">Teaching this term</span>
      {#each c.instructors as instructor}<a
          href={instructorUrl(instructor.instructor_uid)}
          >{instructor.name}<ArrowUpRight size={15} /></a
        >{:else}<span class="muted">No instructors listed</span>{/each}
    </div>
  </div>
  <div class="row course-meta">
    {#if c.statistics?.gpa != null}<a href="#grades" class="course-gpa"
        >{c.statistics.gpa.toFixed(2)} <span>average GPA</span></a
      >{/if}
    <span class:available={c.offerings.length}
      ><i></i>{c.offerings.length
        ? "offered this term"
        : "not currently offered"}</span
    ><span>{credits(c.credits_min, c.credits_max)}</span><span
      >{c.instructors.length}
      {c.instructors.length === 1 ? "instructor" : "instructors"}</span
    >
  </div>
</div>
<nav class="course-jumps" aria-label="Course sections">
  {#each links as link}<a
      href={"#" + link.id}
      aria-current={active === link.id ? "location" : undefined}
      ><link.icon size={14} strokeWidth={1.5} />{link.label}</a
    >{/each}
</nav>
<section class="course-overview" id="overview" aria-label="Course overview">
  <div class="overview-take">
    <div class="overview-heading">
      <h2>What to expect</h2>
      <span class="mono muted">AI summary · sources below</span>
    </div>
    <Claims
      claims={(summary.quick_take || [])
        .filter(
          (claim: any) =>
            !claim.citations?.length ||
            claim.citations.some((citation: any) => citation.type === "review"),
        )
        .slice(0, 1)}
      reviewFiles={c.evidence.reviews}
    />
    {#if summary.difficulty_workload?.length}<div class="overview-workload">
        <span class="teacher-label">Workload</span><Claims
          claims={summary.difficulty_workload.slice(0, 1)}
          reviewFiles={c.evidence.reviews}
        />
      </div>{:else}<p class="muted">No workload feedback recorded.</p>{/if}
    <a class="overview-link" href="#experience"
      >All student feedback <ArrowUpRight size={14} /></a
    >
  </div>
  <GradeSnapshot grades={c.grades} />
</section>
<div class="course-workspace">
  <aside class="course-facts" aria-label="Course details">
    <Panel title="Course details">
      <div class="fact-pair">
        <span>[credits]</span><strong
          >{credits(c.credits_min, c.credits_max)}</strong
        >
      </div>
      <div class="fact-pair">
        <span>[offered]</span><strong
          >{[
            ...new Set(
              c.offerings.map((o: any) => o.typically_offered).filter(Boolean),
            ),
          ].join(" · ") || "Not recorded"}</strong
        >
      </div>
      <div class="fact-pair">
        <span>[subjects]</span>
        <div class="row">
          {#each c.subjects as subject}<a
              href={"/subjects/" + encodeURIComponent(subject)}>{subject}</a
            >{/each}
        </div>
      </div>
      <div class="fact-block">
        <h3><BookOpen size={13} /> Topics</h3>
        <div class="tags">
          {#each c.llm_topics as topic}<span>{topic}</span>{/each}
        </div>
      </div>
      <div class="fact-block">
        <h3><GitBranch size={13} /> Before you enroll</h3>
        <p>{c.requirements_text || "No prerequisites listed."}</p>
        <a class="small-link" href="#requirements"
          >Explore requirements <ArrowUpRight size={12} /></a
        >
      </div>
      <details>
        <summary>Catalog description</summary>
        <p>{c.description}</p>
      </details>
      <details>
        <summary>Skills & assumed background</summary>
        <h3>Skills</h3>
        <ul>
          {#each c.llm_skills as skill}<li>{skill}</li>{/each}
        </ul>
        <h3>Assumed background</h3>
        <ul>
          {#each c.llm_assumed_background as item}<li>{item}</li>{/each}
        </ul>
      </details>
    </Panel>
  </aside>
  <div class="course-content">
    <Panel title="Grades" id="grades">
      <Grades
        grades={c.grades}
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
    <Panel
      title="Student experience"
      id="experience"
      label="AI summary · cited sources"
    >
      <div class="experience-grid">
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
    </Panel>
    <Panel title="Professors" id="professors" label={termName(c.semester)}>
      <div class="professor-grid">
        {#each c.instructors as i}{@const feedback =
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
                <a href={instructorUrl(i.instructor_uid)}
                  >{i.name}<ArrowUpRight size={13} /></a
                >
              </h3>
            </div>
            {#if feedback?.summary?.length}<Claims
                claims={feedback.summary}
                reviewFiles={c.evidence.reviews}
              />{:else}<p class="muted">
                No course-specific feedback yet.
              </p>{/if}
          </article>{:else}<p class="muted">
            No current instructors recorded.
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
    <Panel title="Prerequisites" id="requirements">
      <p class="requirements-source">
        {c.requirements_text || "No prerequisites listed."}
      </p>
      {#if Graph}<Graph ast={c.requirements} />{:else}<div
          class="graph-loading"
        >
          {graphError || "Loading prerequisite tree…"}
        </div>{/if}
      {#if c.requirements.status !== "valid"}<p class="muted mono">
          Best-effort interpretation · check the original requirements above.
        </p>{/if}
      <details>
        <summary>Prerequisite text tree</summary><RequirementText
          ast={c.requirements}
        />
      </details>
    </Panel>
    <Panel
      title="Calendar & sections"
      id="schedule"
      label={termName(c.semester)}
    >
      <CourseCalendar
        files={c.evidence.meetings || []}
        observedAt={c.observed_at}
      />
      <div class="table-scroll">
        <table>
          <thead
            ><tr
              ><th>Section</th><th>Mode</th><th>Enrolled / capacity</th><th
                >Waitlist</th
              ></tr
            ></thead
          ><tbody
            >{#each c.sections as s}<tr
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
      <p class="muted mono">Enrollment at scan time.</p>
      <Evidence
        title="Meeting source records"
        files={c.evidence.meetings || []}
      />
    </Panel>
    <Panel title="Sources & history" id="evidence">
      <details>
        <summary>Current offering source records</summary>
        <pre>{JSON.stringify(c.offerings, null, 2)}</pre>
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
