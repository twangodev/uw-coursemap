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
  <div class="flex items-baseline justify-between gap-5 mb-6 finder-heading">
    <h2 class="text-[27px] font-medium m-0">
      {ranked ? "Find your fit" : "Find your next class"}
    </h2>
    <span class="text-[13px] muted"
      ><strong>{results.total}</strong> courses</span
    >
  </div>
  <form action={path} class="flex items-center gap-3 finder-search">
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
    />{#each Object.entries( { ...urlParams, term: results.term, availability: results.availability } ).filter(([key]) => !["q", "page"].includes(key)) as [key, value]}<input
        type="hidden"
        name={key}
        {value}
      />{/each}<button
      class="grid place-items-center min-h-10.5 border-0 bg-transparent shrink-0 py-2 px-2.5"
      aria-label="Search"><Search size={19} strokeWidth={1.5} /></button
    >
  </form>
  <div class="flex flex-wrap gap-2.5 finder-filters my-5.5 mx-0">
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
  <p class="text-[12px] text-muted max-w-[75ch] mt-4 mb-2 coverage mx-0">
    Historical grades cover up to five years through the selected term. {ranked
      ? "Only courses with at least 100 letter grades are ranked."
      : "Grade sorting prioritizes courses with at least 100 letter grades."}
  </p>
  <CourseList
    courses={results.items}
    rankStart={ranked ? (results.page - 1) * 30 + 1 : undefined}
  />
  <nav
    class="flex gap-6 mt-6 text-[13px] pagination"
    aria-label="Course results pages"
  >
    {#if results.page > 1}<a href={pageLink(results.page - 1)}>← Previous</a
      >{/if}<span>Page {results.page}</span
    >{#if results.page * 30 < results.total}<a href={pageLink(results.page + 1)}
        >Next →</a
      >{/if}
  </nav>
</section>

<style>
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
</style>
