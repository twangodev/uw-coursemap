<script lang="ts">
  import { courseUrl, credits, courseTitle } from "$lib/format";
  import type { CourseCard } from "$lib/types";
  let { courses }: { courses: CourseCard[] } = $props();
</script>

<div>
  {#each courses as c}<a class="course-row" href={courseUrl(c.course_uid)}
      ><span class="code">{c.course_id}</span><span
        class="course-title"
        title={c.title}>{courseTitle(c.title)}</span
      ><span class="muted mono"
        >{credits(c.credits_min, c.credits_max)}{c.gpa != null
          ? ` · ${c.gpa.toFixed(2)} GPA`
          : ""}</span
      ></a
    >{:else}<p class="empty">No courses found.</p>{/each}
</div>
