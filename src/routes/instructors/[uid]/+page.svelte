<script lang="ts">
  import StudentReviews from "$lib/components/StudentReviews.svelte";
  import Select from "$lib/components/Select.svelte";
  import { goto } from "$app/navigation";
  import InstructorStats from "$lib/components/InstructorStats.svelte";
  import TeachingTimeline from "$lib/components/TeachingTimeline.svelte";
  import CourseList from "$lib/components/CourseList.svelte";
  import { courseUrl, termName, courseTitle } from "$lib/format";
  let { data } = $props();
  let history = $state<any[]>([]);
  let page = $state(1);
  let end = $state(false);
  let failure = $state("");
  let loading = $state(false);
  async function more() {
    if (loading) return;
    loading = true;
    failure = "";
    try {
      const r = await fetch(
        `/api/instructors/${data.instructor.instructor_uid}/history?page=${page + 1}&revision=${data.status.revision}`,
      );
      if (!r.ok)
        throw new Error(
          "History unavailable. Reload to check for a dataset update.",
        );
      const body: any = await r.json();
      history = [...history, ...body.items];
      page++;
      end = body.items.length < 100;
    } catch (e) {
      failure = (e as Error).message;
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>{data.instructor.name} · UW Courses</title></svelte:head>
<div class="hero">
  <p class="mono muted">
    {data.instructor.current ? "Current instructor" : "Historical instructor"}
  </p>
  <h1>{data.instructor.name || "Name unavailable"}</h1>
</div>
<InstructorStats ratings={data.instructor.ratings} />
<StudentReviews
  initial={data.reviews}
  uid={data.instructor.instructor_uid}
  revision={data.status.revision}
/>
<section class="section">
  <div class="teaching-heading">
    <h2>Classes with {data.instructor.name || "this instructor"}</h2>
    <Select
      label="Teaching term"
      value={data.term}
      options={[
        ...new Set([
          data.status.term,
          ...data.timeline.map((row: any) => row.term),
        ]),
      ]
        .sort()
        .reverse()
        .map((term) => ({ value: term, label: termName(term) }))}
      onChange={(term) =>
        goto(`?term=${term}`, { noScroll: true, keepFocus: true })}
    />
  </div>
  {#if !data.courses.length}<p class="muted">
      No teaching recorded in {termName(data.term)}.
    </p>
    {#if data.timeline.length && data.timeline.at(-1)?.term !== data.term}<a
        href={`?term=${data.timeline.at(-1)?.term}`}
        >View last recorded teaching term →</a
      >{/if}{/if}
  <CourseList courses={data.courses} />
</section>
<section class="section">
  <h2>Recorded teaching history</h2>
  <TeachingTimeline terms={data.timeline} /><a
    href={"/search?instructor=" + data.instructor.instructor_uid}
    >Explore courses taught by this instructor →</a
  >
  <details>
    <summary>Browse recorded courses</summary>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Term</th><th>Course</th><th>Title</th></tr></thead><tbody
          >{#each [...data.history, ...history] as r}<tr
              ><td>{termName(r.term)}</td><td
                ><a href={courseUrl(r.course_uid)}>{r.course_id}</a></td
              ><td>{courseTitle(r.title)}</td></tr
            >{/each}</tbody
        >
      </table>
    </div>
    {#if data.history.length === 100 && !end}<button
        onclick={more}
        disabled={loading}>{loading ? "Loading…" : "Load more history"}</button
      >{/if}{#if failure}<p role="alert">{failure}</p>{/if}
  </details>
  <p class="muted">
    Teaching history may be incomplete. Course pages contain course-specific
    feedback and citations.
  </p>
</section>
<details>
  <summary>Instructor identity & provenance</summary>
  <pre>{JSON.stringify(data.instructor, null, 2)}</pre>
</details>

<style>
  .teaching-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 28px;
  }
  .teaching-heading h2 {
    font-size: 27px;
    font-weight: 500;
  }
  .hero {
    padding-bottom: 24px;
  }
  @media (max-width: 700px) {
    .teaching-heading {
      align-items: start;
      flex-direction: column;
    }
  }
</style>
