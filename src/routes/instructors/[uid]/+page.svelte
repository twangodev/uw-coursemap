<script lang="ts">
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
<InstructorStats
  ratings={data.instructor.ratings}
  grades={data.instructor.grade_statistics}
/>
<section class="section">
  <h2>Teaching in {termName(data.status.term)}</h2>
  <CourseList courses={data.instructor.courses} />
</section>
<section class="section">
  <h2>Recorded teaching history</h2>
  <TeachingTimeline terms={data.timeline} /><a
    href={"/search?instructor=" + data.instructor.instructor_uid}
    >Explore courses taught by this instructor →</a
  >
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
  <p class="muted">
    Teaching history may be incomplete. Course pages contain course-specific
    feedback and citations.
  </p>
</section>
<details>
  <summary>Instructor identity & provenance</summary>
  <pre>{JSON.stringify(data.instructor, null, 2)}</pre>
</details>
