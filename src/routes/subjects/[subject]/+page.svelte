<script lang="ts">
  import CourseList from "$lib/components/CourseList.svelte";
  let { data } = $props();
</script>

<svelte:head><title>{data.subject} · UW Courses</title></svelte:head>
<div class="hero">
  <a class="mono muted" href="/subjects">← Departments</a>
  <h1>{data.subject}</h1>
  <p class="muted">{data.courses.length} courses</p>
</div>
<CourseList courses={data.courses} />
