<script lang="ts">
  import type { CourseResults } from "$lib/view-models";
  import type { Status } from "$lib/types";
  import { departmentLabel } from "$lib/departments";
  import { Search } from "@lucide/svelte";
  import { goto } from "$app/navigation";
  import SearchInput from "./SearchInput.svelte";
  import Select from "./Select.svelte";
  import CourseList from "./CourseList.svelte";
  import { termName } from "$lib/format";
  let {
    results,
    status,
    subject = "",
    path = "/search",
    showTerm = true,
    ranked = false,
  }: {
    results: CourseResults;
    status: Status;
    subject?: string;
    path?: string;
    showTerm?: boolean;
    ranked?: boolean;
  } = $props();
  function change(key: string, value: string) {
    const query = new URLSearchParams(location.search);
    query.set(key, value);
    query.delete("page");
    goto(`${path}?${query}`, { keepFocus: true, noScroll: true });
  }
  let urlParams = $derived(results.filters || {});
  function pageLink(page: number) {
    const query = new URLSearchParams({ ...urlParams, page: String(page) });
    return `${path}?${query}`;
  }
</script>

<section aria-label="Find courses" class="finder">
  <div class="finder-heading">
    <h2>{ranked ? "Find your fit" : "Find your next class"}</h2>
    <span class="muted"><strong>{results.total}</strong> courses</span>
  </div>
  <form action={path} class="finder-search">
    <SearchInput
      value={results.q}
      revision={status.revision}
      filters={{
        ...urlParams,
        subject: subject || urlParams.subject || "",
        term: results.term,
        availability: results.availability,
      }}
      placeholder="A course, professor, or something you want to learn…"
    />{#each Object.entries( { ...urlParams, term: results.term, availability: results.availability }, ).filter(([key]) => !["q", "page"].includes(key)) as [key, value]}<input
        type="hidden"
        name={key}
        {value}
      />{/each}<button aria-label="Search"><Search size={19} strokeWidth={1.5} /></button>
  </form>
  <div class="finder-filters">
    {#if !subject}<Select
        label="Department"
        value={urlParams.subject || ""}
        options={[
          { value: "", label: "All departments" },
          ...status.departments.map((d) => ({
            value: d.subject,
            label: departmentLabel(d.subject),
          })),
        ]}
        onChange={(v) => change("subject", v)}
      />{/if}
    {#if showTerm}
      <Select
        label="Term"
        value={results.term}
        options={status.terms.map((term: string) => ({
          value: term,
          label: termName(term),
        }))}
        onChange={(v) => change("term", v)}
      />
    {/if}
    <Select
      label="Course availability"
      value={results.availability}
      options={[
        { value: "offered", label: "Recorded offerings" },
        { value: "all", label: "Full catalog" },
      ]}
      onChange={(v) => change("availability", v)}
    />
    <Select
      label="Course level"
      value={urlParams.level || ""}
      options={[
        { value: "", label: "All levels" },
        ...Array.from({ length: 10 }, (_, i) => ({
          value: String(i * 100),
          label: `${i * 100}–${i * 100 + 99} level`,
        })),
      ]}
      onChange={(v) => change("level", v)}
    />
    <Select
      label="Credits"
      value={urlParams.credits_max || ""}
      options={[
        { value: "", label: "Any credits" },
        { value: "1", label: "Up to 1 credit" },
        { value: "3", label: "Up to 3 credits" },
        { value: "4", label: "Up to 4 credits" },
      ]}
      onChange={(v) => change("credits_max", v)}
    />
    {#if !ranked}<Select
      label="Sort courses"
      value={urlParams.sort || ""}
      options={[
        { value: "", label: "Course match" },
        { value: "gpa", label: "Higher historical grades" },
      ]}
      onChange={(v) => change("sort", v)}
    />{/if}
  </div>
  <p class="coverage">
    Historical grades cover up to five years through the selected term. {ranked ? "Only courses with at least 100 letter grades are ranked." : "Grade sorting prioritizes courses with at least 100 letter grades."}
  </p>
  <CourseList courses={results.items} rankStart={ranked ? (results.page - 1) * 30 + 1 : undefined} />
  <nav class="pagination" aria-label="Course results pages">
    {#if results.page > 1}<a href={pageLink(results.page - 1)}>← Previous</a
      >{/if}<span>Page {results.page}</span
    >{#if results.page * 30 < results.total}<a href={pageLink(results.page + 1)}
        >Next →</a
      >{/if}
  </nav>
</section>

<style>
  .finder-heading {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 24px;
  }
  .finder-heading h2 {
    font-size: 27px;
    font-weight: 500;
    margin: 0;
  }
  .finder-heading span {
    font-size: 13px;
  }
  .finder-search {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .finder-search > button { display: grid; place-items: center; min-height: 42px; padding: 8px 10px; border: 0; background: transparent; flex-shrink: 0; }
  .finder-search :global(.search-input) {
    flex: 1;
    min-width: 0;
    padding: 0;
    border: 0;
    border-bottom: 1px solid var(--border);
    background: transparent;
    color: var(--text);
    font: inherit;
  }
  .finder-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 22px 0;
  }
  .coverage {
    font-size: 12px;
    color: var(--muted);
    max-width: 75ch;
    margin: 16px 0 8px;
  }
  .pagination {
    display: flex;
    gap: 24px;
    margin-top: 24px;
    font-size: 13px;
  }
</style>
