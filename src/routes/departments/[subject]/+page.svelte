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

<div class="hero">
  <a class="muted" href="/departments">← Departments</a>
  <p class="mono department-code">{data.subject}</p>
  <h1>{name}</h1>
  <p class="muted">Get a feel for the department. Find your next class.</p>
</div>
<a class="small-link" href={`/explorer/${encodeURIComponent(data.subject)}`}>Explore prerequisite map →</a>
<p><a href={`/departments/${encodeURIComponent(data.subject)}/catalog`}>Browse all {name} courses →</a></p>
<CourseCollections subject={data.subject} term={data.results.term} />
<DepartmentStats stats={data.stats} />
<div class="term-toolbar">
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
<div class="department-finder">
  <CourseFinder
    showTerm={false}
    results={data.results}
    status={data.status}
    subject={data.subject}
    path={page.url.pathname}
  />
</div>

<style>
  .department-code { margin: 22px 0 10px; color: var(--accent); font-size: 13px; }
  .term-toolbar {
    display: flex;
    justify-content: flex-end;
    margin: 28px 0 8px;
  }
  .hero {
    padding-bottom: 36px;
  }
  .department-finder {
    margin: 40px 0 48px;
  }
</style>
