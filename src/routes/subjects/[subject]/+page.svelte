<script lang="ts">
  import { departmentName, departmentLabel } from "$lib/departments";
  import CourseCollections from "$lib/components/CourseCollections.svelte";
  import Select from "$lib/components/Select.svelte";
  import { goto } from "$app/navigation";
  import { termName } from "$lib/format";
  import CourseFinder from "$lib/components/CourseFinder.svelte";
  import DepartmentStats from "$lib/components/DepartmentStats.svelte";
  let { data } = $props();
  let name = $derived(departmentName(data.subject));
  let title = $derived(`${departmentLabel(data.subject)} Courses, Grades & Reviews · UW Courses`);
  let description = $derived(`Explore ${name} courses at UW–Madison. Compare historical grades, instructors and student reviews, and find the easiest and hardest courses in ${name}.`);
</script>

<svelte:head><title>{title}</title><meta name="description" content={description} /><meta property="og:title" content={title} /><meta property="og:description" content={description} /></svelte:head>
<div class="hero">
  <a class="muted" href="/subjects">← Departments</a>
  <p class="mono department-code">{data.subject}</p>
  <h1>{name}</h1>
  <p class="muted">Get a feel for the department. Find your next class.</p>
</div>
<CourseCollections subject={data.subject} term={data.results.term} />
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
      goto(`?${query}`, { noScroll: true, keepFocus: true });
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
