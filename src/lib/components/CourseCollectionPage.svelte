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

<svelte:head
  ><title
    >{collection.title}{data.results.filters.subject
      ? ` · ${departmentLabel(data.results.filters.subject)}`
      : ""} · UW Courses</title
  ><meta name="description" content={`${collection.description}${data.results.filters.subject ? ` Explore ${departmentName(data.results.filters.subject)} at UW–Madison.` : ""}`} /></svelte:head
>
<div class="collection-heading">
  <a
    class="muted"
    href={data.results.filters.subject
      ? `/subjects/${encodeURIComponent(data.results.filters.subject)}`
      : "/search"}>← {data.results.filters.subject ? departmentLabel(data.results.filters.subject) : "Explore courses"}</a
  >
  <h1>{collection.title}{data.subject ? ` in ${departmentName(data.subject)}` : ""}</h1>
  <p>{collection.description}</p>
  <p class="muted method">
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
    ? `/subjects/${encodeURIComponent(data.subject)}/${data.collection}`
    : `/courses/${data.collection}`}
  ranked
/>

<style>
  .collection-heading {
    padding: 20px 0 24px;
    max-width: 760px;
  }
  h1 {
    margin: 20px 0 16px;
  }
  p {
    line-height: 1.7;
  }
  .method {
    font-size: 13px;
    margin-top: 16px;
  }
</style>
