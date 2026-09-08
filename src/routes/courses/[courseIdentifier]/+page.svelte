<script lang="ts">
  import { onMount } from "svelte";
  let interactive = $state(false);
  onMount(() => {
    interactive = true;
  });
  import Claims from "$lib/components/Claims.svelte";
  import Evidence from "$lib/components/Evidence.svelte";
  import Grades from "$lib/components/Grades.svelte";
  import RequirementText from "$lib/components/RequirementText.svelte";
  import { credits, instructorUrl, termName } from "$lib/format";
  let { data } = $props();
  let c = $derived(data.course);
  let summary = $derived(c.student_summary);
  let offeringLabels = $derived([
    ...new Set<string>(
      c.offerings.map(
        (o: any) =>
          `${termName(o.term_id)} · ${credits(o.credits_min, o.credits_max)}${o.typically_offered ? ` · Typically ${o.typically_offered}` : ""}`,
      ),
    ),
  ]);
  let Graph = $state<any>(null);
  let graphError = $state("");
  async function showGraph() {
    try {
      Graph = (await import("$lib/components/RequirementGraph.svelte")).default;
    } catch {
      graphError = "Unable to load graph. The complete text tree is below.";
    }
  }
</script>

<svelte:head
  ><title>{c.course_id} · {c.title} · UW Courses</title><meta
    name="description"
    content={c.llm_summary || c.description?.slice(0, 160)}
  /></svelte:head
>
<div class="hero">
  <div class="row eyebrow">
    {#each c.subjects as s}<a href={"/subjects/" + encodeURIComponent(s)}>{s}</a
      >{/each}<span>· {termName(c.semester)}</span>
  </div>
  <p class="mono accent">{c.course_id}</p>
  <h1>{c.title}</h1>
  <div class="row">
    <span class="pill">{credits(c.credits_min, c.credits_max)}</span><span
      class="muted"
      >{c.offerings.length
        ? "Offered this term"
        : "Not in current offerings"}</span
    >
  </div>
  <p class="reading">{c.llm_summary || c.description}</p>
  <nav class="row mono" aria-label="Course sections">
    <a href="#experience">The class</a><a href="#professors">Professors</a><a
      href="#grades">Grades</a
    ><a href="#requirements">Requirements</a><a href="#evidence"
      >Sources & history</a
    >
  </nav>
</div>
<section class="section" id="experience">
  <h2>What’s the class like?</h2>
  <div class="stack">
    <Claims
      claims={summary.quick_take || []}
      reviewFiles={c.evidence.reviews}
    />{#if !summary.quick_take?.length}<p>
        {c.description}
      </p>{/if}{#if summary.difficulty_workload?.length}<h3>
        Difficulty & workload
      </h3>
      <Claims
        claims={summary.difficulty_workload}
        reviewFiles={c.evidence.reviews}
      />{/if}{#if summary.student_experience?.length}<h3>Student experience</h3>
      <Claims
        claims={summary.student_experience}
        reviewFiles={c.evidence.reviews}
      />{/if}
    <p class="muted">
      Student feedback reflects individual reviewers’ experiences. Summaries are
      AI-generated.
    </p>
    <details>
      <summary>Catalog description & learning topics</summary>
      <div class="stack">
        <p>{c.description}</p>
        <h3>Topics</h3>
        <ul>
          {#each c.llm_topics as topic}<li>{topic}</li>{/each}
        </ul>
        <h3>Skills</h3>
        <ul>
          {#each c.llm_skills as skill}<li>{skill}</li>{/each}
        </ul>
        <h3>Assumed background</h3>
        <ul>
          {#each c.llm_assumed_background as item}<li>{item}</li>{/each}
        </ul>
      </div>
    </details>
  </div>
</section>
<section class="section" id="professors">
  <h2>Who’s teaching?</h2>
  <p class="eyebrow">{termName(c.semester)}</p>
  <div class="stack">
    {#each c.instructors as i}{@const feedback =
        summary.current_instructors?.find(
          (r: any) => r.instructor_uid === i.instructor_uid,
        )}
      <div class="section">
        <h3><a href={instructorUrl(i.instructor_uid)}>{i.name}</a></h3>
        {#if feedback?.summary?.length}<Claims
            claims={feedback.summary}
            reviewFiles={c.evidence.reviews}
          />{:else}<p class="muted">
            No course-specific reviews available.
          </p>{/if}
      </div>{:else}<p class="empty">No current instructors recorded.</p>{/each}
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
</section>
<section class="section" id="grades">
  <h2>How have students performed?</h2>
  <Grades
    grades={c.grades}
    uid={c.course_uid}
    revision={c.revision}
    instructors={c.grade_instructors || c.instructors}
  />{#if c.grade_conflicts?.length}<details>
      <summary
        >Conflicting source distributions · excluded from calculated GPA</summary
      >
      <pre>{JSON.stringify(c.grade_conflicts, null, 2)}</pre>
    </details>{/if}
</section>
<section class="section" id="requirements">
  <h2>Can I take it?</h2>
  <p>{c.requirements_text || "No prerequisites listed."}</p>
  {#if c.requirements.status !== "valid"}<p class="muted mono">
      Best-effort interpretation · check the original requirements above.
    </p>{/if}
  <div class="section">
    {#if Graph}<Graph ast={c.requirements} />{:else}<button
        onclick={showGraph}
        disabled={!interactive}>Explore prerequisite graph</button
      >{/if}{#if graphError}<p>{graphError}</p>{/if}
    <details open>
      <summary>Prerequisite text tree</summary><RequirementText
        ast={c.requirements}
      />
    </details>
  </div>
</section>
<section class="section">
  <h2>Offerings & sections</h2>
  {#each offeringLabels as label}<p>{label}</p>{/each}
  <details>
    <summary>{c.sections.length} current sections</summary>
    <div class="table-scroll">
      <table>
        <thead
          ><tr
            ><th>Section</th><th>Mode</th><th>Enrollment at scan</th><th
              >Waitlist</th
            ></tr
          ></thead
        ><tbody
          >{#each c.sections as s}<tr
              ><td>{s.section_type} {s.section_number}</td><td
                >{s.instruction_mode || "—"}</td
              ><td>{s.enrolled ?? "—"} / {s.capacity ?? "—"}</td><td
                >{s.waitlisted ?? "—"}</td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
  </details>
  <Evidence
    title="Meeting dates & locations"
    files={c.evidence.meetings || []}
  />
</section>
<section class="section" id="evidence">
  <h2>Sources & history</h2>
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
</section>
