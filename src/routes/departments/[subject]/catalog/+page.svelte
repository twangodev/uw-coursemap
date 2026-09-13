<script lang="ts">
  import { departmentName } from "$lib/departments";
  import { courseUrl, courseTitle, credits } from "$lib/format";
  let { data } = $props();
</script>

<nav class="mb-8" aria-label="Breadcrumb">
  <a href="/departments">Departments</a> /
  <a href={`/departments/${encodeURIComponent(data.subject)}`}
    >{departmentName(data.subject)}</a
  > / Course catalog
</nav>
<h1>{departmentName(data.subject)} course catalog</h1>
<p class="leading-[1.7] muted">
  All {data.catalog.length} recorded UW–Madison courses in this department, including
  courses not offered this term. Open a course for prerequisites, historical grades
  and instructors.
</p>
<ul class="list-none p-0 max-w-[85ch] catalog">
  {#each data.catalog as course}
    <li class="border-t border-t-border py-6 px-0">
      <h2 class="text-[1.15rem]">
        <a href={courseUrl(course.course_id)}
          >{course.course_id}: {courseTitle(course.title)}</a
        >
      </h2>
      <p class="leading-[1.7] muted">
        {credits(course.credits_min, course.credits_max)}
      </p>
      {#if course.description}<p class="leading-[1.7]">
          {course.description}
        </p>{/if}
    </li>
  {/each}
</ul>
