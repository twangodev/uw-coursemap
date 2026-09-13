<script lang="ts">
  import { page } from "$app/state";
  import { departmentName, departmentLabel } from "$lib/departments";
  import CourseCollections from "$lib/components/CourseCollections.svelte";
  import TermPicker from "$lib/components/TermPicker.svelte";
  import { goto } from "$app/navigation";
  import { termName } from "$lib/format";
  import CourseFinder from "$lib/components/CourseFinder.svelte";
  import DepartmentStats from "$lib/components/DepartmentStats.svelte";
  let { data } = $props();
  let name = $derived(departmentName(data.subject));
</script>

<div class="pb-9 hero">
  <a class="muted" href="/departments">← Departments</a>
  <p class="mt-5.5 mb-2.5 text-accent text-[13px] mono department-code mx-0">
    {data.subject}
  </p>
  <h1>{name}</h1>
  <p class="muted">Get a feel for the department. Find your next class.</p>
</div>
<a class="small-link" href={`/explorer/${encodeURIComponent(data.subject)}`}
  >Explore prerequisite map →</a
>
<p>
  <a href={`/departments/${encodeURIComponent(data.subject)}/catalog`}
    >Browse all {name} courses →</a
  >
</p>
<CourseCollections subject={data.subject} term={data.results.term} />
<DepartmentStats stats={data.stats} />
<div class="flex justify-end mt-7 mb-2 term-toolbar mx-0">
  <TermPicker
    label="Term"
    value={data.results.term}
    terms={data.status.terms}
    onChange={(term) => {
      const query = new URLSearchParams(location.search);
      query.set("term", term);
      query.delete("page");
      goto(`?${query}`, { noScroll: true, keepFocus: true });
    }}
  />
</div>
<DepartmentStats stats={data.stats} term={data.results.term} />
<DepartmentStats stats={data.stats} term={data.results.term} detail />
<div class="mt-10 mb-12 department-finder mx-0">
  <CourseFinder
    showTerm={false}
    results={data.results}
    status={data.status}
    subject={data.subject}
    path={page.url.pathname}
  />
</div>
