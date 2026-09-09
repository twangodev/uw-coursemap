<script lang="ts">
  import { departmentName } from "$lib/departments";
  import { courseUrl, courseTitle, credits } from "$lib/format";
  let { data } = $props();
</script>

<nav aria-label="Breadcrumb">
  <a href="/departments">Departments</a> /
  <a href={`/departments/${encodeURIComponent(data.subject)}`}
    >{departmentName(data.subject)}</a
  > / Course catalog
</nav>
<h1>{departmentName(data.subject)} course catalog</h1>
<p class="muted">
  All {data.catalog.length} recorded UW–Madison courses in this department, including
  courses not offered this term. Open a course for prerequisites, historical grades
  and instructors.
</p>
<ul class="catalog">
  {#each data.catalog as course}
    <li>
      <h2>
        <a href={courseUrl(course.course_id)}
          >{course.course_id}: {courseTitle(course.title)}</a
        >
      </h2>
      <p class="muted">{credits(course.credits_min, course.credits_max)}</p>
      {#if course.description}<p>{course.description}</p>{/if}
    </li>
  {/each}
</ul>

<style>
  nav {
    margin-bottom: 2rem;
  }
  .catalog {
    list-style: none;
    padding: 0;
    max-width: 85ch;
  }
  li {
    border-top: 1px solid var(--border);
    padding: 1.5rem 0;
  }
  h2 {
    font-size: 1.15rem;
  }
  p {
    line-height: 1.7;
  }
</style>
