<script lang="ts">
  import { onMount } from "svelte";
  import { courseUrl, normalize } from "$lib/format";
  import { departmentName } from "$lib/departments";
  import type { CourseMapData } from "$lib/course-map";
  let { data }: { data: { subject: string | null; graph: CourseMapData } } =
    $props();
  let Graph = $state<any>(null);
  let query = $state("");
  let chosen = $state("");
  let candidates = $derived(
    data.graph.courses
      .filter(
        (course) =>
          (!data.subject || course.subjects.includes(data.subject)) &&
          `${course.code} ${course.title}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      )
      .sort((a, b) => Number(a.code.split(" ").at(-1)) - Number(b.code.split(" ").at(-1)) || a.code.localeCompare(b.code)).slice(0, 8),
  );
  let focus = $derived(
    chosen ||
      data.graph.courses.find((course) => course.code === "COMPSCI 300")?.uid ||
      candidates[0]?.uid ||
      data.graph.courses[0]?.uid,
  );
  let title = $derived(
    data.subject
      ? `${departmentName(data.subject)} prerequisite map`
      : "Course prerequisite map",
  );
  onMount(() => {
    const requested = new URL(location.href).searchParams.get("course");
    if (requested)
      chosen =
        data.graph.courses.find(
          (course) => normalize(course.code) === normalize(requested),
        )?.uid || "";
    import("./CourseMap.svelte").then((module) => (Graph = module.default));
  });
</script>

<svelte:head
  ><title>{title} · UW Courses</title><meta
    name="description"
    content={`Explore course prerequisite relationships${data.subject ? ` in ${departmentName(data.subject)}` : " at UW–Madison"}.`}
  /></svelte:head
>
<div class="hero">
  <a href="/explorer" class="muted">← Prerequisite maps</a>
  <h1>{title}</h1>
  <p>See what comes before a course—and what it can lead to.</p>
  {#if data.subject}<a href={`/departments/${encodeURIComponent(data.subject)}`}
      >Department courses & statistics →</a
    >{/if}
</div>
<label for="map-search">Find a course on the map</label><input
  id="map-search"
  type="search"
  placeholder="Course code or title…"
  bind:value={query}
/>
<div class="map-choices">
  {#each candidates as course}<button
      class:active={focus === course.uid}
      onclick={() => (chosen = course.uid)}>{course.code}</button
    >{/each}
</div>
{#if Graph && focus}<Graph data={data.graph} {focus} />{:else}<p class="muted">
    Loading prerequisite map…
  </p>{/if}
<p class="map-note muted">
  Arrows show course references from the parsed prerequisites, including
  alternatives. They do not mean every linked course is required. Open a course
  for its complete requirements and exclusions.
</p>
<details>
  <summary>Course links</summary>
  <ul>
    {#each candidates as course}<li>
        <a href={courseUrl(course.code)}>{course.code} · {course.title}</a>
      </li>{/each}
  </ul>
</details>

<style>
  .hero {
    padding-bottom: 32px;
  }
  .hero h1 {
    margin-top: 20px;
  }
  label {
    display: block;
    margin-bottom: 10px;
    font-size: 13px;
  }
  input {
    width: min(100%, 460px);
  }
  .map-choices {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 16px 0 24px;
  }
  button {
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--muted);
    background: transparent;
    cursor: pointer;
  }
  button.active {
    color: var(--accent);
    border-color: var(--accent);
  }
  .map-note {
    max-width: 85ch;
    margin: 24px 0;
    line-height: 1.7;
    font-size: 13px;
  }
</style>
