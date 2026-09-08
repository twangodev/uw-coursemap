<script lang="ts">
  import Select from "$lib/components/Select.svelte";
  import { goto } from "$app/navigation";
  import { termName } from "$lib/format";
  import CourseFinder from "$lib/components/CourseFinder.svelte";
  import DepartmentStats from "$lib/components/DepartmentStats.svelte";
  let { data } = $props();
</script>

<svelte:head><title>{data.subject} · UW Courses</title></svelte:head>
<div class="hero">
  <a class="muted" href="/subjects">← Departments</a>
  <h1>{data.subject}</h1>
  <p class="muted">Get a feel for the department. Find your next class.</p>
</div>
<DepartmentStats stats={data.stats} />
<div class="term-toolbar">
  <Select
    label="Term"
    value={data.results.term}
    options={data.status.terms.map((term: string) => ({
      value: term,
      label: termName(term),
    }))}
    onChange={(term) => {
      const query = new URLSearchParams(location.search);
      query.set("term", term);
      query.delete("page");
      goto(`?${query}`, { noScroll: true });
    }}
  />
</div>
<DepartmentStats stats={data.stats} term={data.results.term} />
<div class="department-finder">
  <CourseFinder
    showTerm={false}
    results={data.results}
    status={data.status}
    subject={data.subject}
    path={`/subjects/${encodeURIComponent(data.subject)}`}
  />
</div>

<DepartmentStats stats={data.stats} term={data.results.term} detail />

<style>
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
