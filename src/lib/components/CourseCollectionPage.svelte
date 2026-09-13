<script lang="ts">
  import { departmentName, departmentLabel } from "$lib/departments";
  import CourseFinder from "$lib/components/CourseFinder.svelte";
  import CourseCollections from "$lib/components/CourseCollections.svelte";
  import {
    courseCollections,
    type CourseCollection,
  } from "$lib/course-collections";
  let { data }: { data: any } = $props();
  let collection = $derived(
    courseCollections[data.collection as CourseCollection],
  );
</script>

<div class="pt-5 pb-6 max-w-190 collection-heading px-0">
  <a
    class="muted"
    href={data.results.filters.subject
      ? `/departments/${encodeURIComponent(data.results.filters.subject)}`
      : "/search"}
    >← {data.results.filters.subject
      ? departmentLabel(data.results.filters.subject)
      : "Explore courses"}</a
  >
  <h1 class="mt-5 mb-4 mx-0">
    {collection.title}{data.subject
      ? ` in ${departmentName(data.subject)}`
      : ""}
  </h1>
  <p class="leading-[1.7]">{collection.description}</p>
  <p class="leading-[1.7] text-[13px] mt-4 muted method">
    {collection.method} At least 100 letter grades over the five years through the
    selected term. Grades reflect past outcomes, not workload or a guaranteed result.
  </p>
</div>
<CourseCollections
  subject={data.results.filters.subject || ""}
  term={data.results.term}
  active={data.collection}
/>
<CourseFinder
  results={data.results}
  status={data.status}
  subject={data.subject || ""}
  path={data.subject
    ? `/departments/${encodeURIComponent(data.subject)}/${data.collection}`
    : `/courses/${data.collection}`}
  ranked
/>
