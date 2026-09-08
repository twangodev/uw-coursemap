<script lang="ts">
  import InstructorFilter from "$lib/components/InstructorFilter.svelte";
  let instructor = $state("");
  import { page } from "$app/state";
  import { onDestroy } from "svelte";
  import CourseList from "$lib/components/CourseList.svelte";
  import { instructorUrl, termName } from "$lib/format";
  let { data } = $props();
  let form: HTMLFormElement;
  let timer: ReturnType<typeof setTimeout>;
  let controller: AbortController | undefined;
  let live = $state<any>(null);
  let loading = $state(false);
  let message = $state("");
  $effect(() => {
    data.results;
    instructor = page.url.searchParams.get("instructor") || "";
    live = null;
  });
  async function preview() {
    clearTimeout(timer);
    controller?.abort();
    timer = setTimeout(async () => {
      const params = new URLSearchParams(new FormData(form) as any);
      params.set("revision", data.status.revision);
      controller = new AbortController();
      loading = true;
      try {
        const r = await fetch("/api/search?" + params, {
          signal: controller.signal,
        });
        if (!r.ok)
          throw new Error(
            r.status === 409
              ? "Dataset updated. Reload this page."
              : "Search unavailable. Please try again.",
          );
        live = await r.json();
        message = "";
        const u = new URL(location.href);
        u.search = new URLSearchParams(new FormData(form) as any).toString();
        history.replaceState(history.state, "", u);
      } catch (e) {
        if ((e as Error).name !== "AbortError") message = (e as Error).message;
      } finally {
        loading = false;
      }
    }, 200);
  }
  onDestroy(() => {
    clearTimeout(timer);
    controller?.abort();
  });
  let result = $derived(live || data.results);
  function pageUrl(n: number) {
    const p = new URLSearchParams(
      typeof location !== "undefined" ? location.search : page.url.search,
    );
    p.set("page", String(n));
    return "/search?" + p;
  }
</script>

<svelte:head
  ><title>Explore courses · UW Courses</title><meta
    name="robots"
    content="noindex,follow"
  /></svelte:head
>
<div class="search-heading">
  <h1>Explore courses</h1>
  <span class="mono muted">{termName(data.status.term)}</span>
</div>
<form
  bind:this={form}
  action="/search"
  oninput={preview}
  onchange={preview}
  class="search-form"
>
  <div class="search-entry">
    <label class="sr-only" for="q">Search</label><input
      class="searchbox"
      id="q"
      name="q"
      value={data.results.q}
      placeholder="CS 300, machine learning, a professor…"
    /><button class="button-primary">Search</button>
  </div>
  <div class="filters primary-filters">
    <label
      >Search for<select name="kind" value={data.results.kind}
        ><option value="course">Courses</option><option value="instructor"
          >Instructors</option
        ></select
      ></label
    >
    <label
      >Department<select
        name="subject"
        value={page.url.searchParams.get("subject") || ""}
        ><option value="">All departments</option
        >{#each data.status.departments as d}<option>{d.subject}</option
          >{/each}</select
      ></label
    >
    <label
      >Term<select name="term" value={page.url.searchParams.get("term") || ""}
        ><option value="">All recorded terms</option
        >{#each data.status.terms || [data.status.term] as term}<option
            value={term}>{termName(term)}</option
          >{/each}</select
      ></label
    >
    <label
      >Sort<select name="sort" value={page.url.searchParams.get("sort") || ""}
        ><option value="">Relevance</option><option value="gpa"
          >Highest GPA</option
        ></select
      ></label
    >
  </div>
  <details
    class="advanced-filters"
    open={["instructor", "credits_min", "credits_max", "gpa_min"].some((key) =>
      page.url.searchParams.get(key),
    )}
  >
    <summary>More filters</summary>
    <div class="filters">
      <InstructorFilter
        bind:value={instructor}
        revision={data.status.revision}
        onchange={preview}
      />
      <label
        >Min credits<input
          type="number"
          name="credits_min"
          min="0"
          value={page.url.searchParams.get("credits_min") || ""}
        /></label
      >
      <label
        >Max credits<input
          type="number"
          name="credits_max"
          min="0"
          value={page.url.searchParams.get("credits_max") || ""}
        /></label
      >
      <label
        >Min GPA<input
          type="number"
          name="gpa_min"
          min="0"
          max="4"
          step=".1"
          value={page.url.searchParams.get("gpa_min") || ""}
        /></label
      >
    </div>
  </details>
</form>
<p class="muted mono result-count" aria-live="polite">
  {message ||
    `${result.total.toLocaleString()} results${loading ? " · searching…" : ""}`}
</p>
{#if result.kind === "course"}<CourseList
    courses={result.items}
  />{:else}{#each result.items as i}<a
      class="course-row"
      href={instructorUrl(i.instructor_uid)}
      ><span>{i.name || "Name unavailable"}</span><span class="muted"
        >{i.current
          ? `Teaching in ${termName(data.status.term)}`
          : "Historical instructor"}</span
      ></a
    >{/each}{/if}
<nav class="row section" aria-label="Results pages">
  {#if result.page > 1}<a href={pageUrl(result.page - 1)}>← Previous</a
    >{/if}<span class="mono">Page {result.page}</span
  >{#if result.page * 30 < result.total}<a href={pageUrl(result.page + 1)}
      >Next →</a
    >{/if}
</nav>

<style>
  .search-heading {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    align-items: center;
    padding: 14px 0 26px;
  }
  h1 {
    font-size: 36px;
  }
  .search-entry {
    display: flex;
    gap: 12px;
  }
  .searchbox {
    min-width: 0;
    flex: 1;
    padding: 14px 18px;
    font-size: 18px;
  }
  .search-entry button {
    padding-inline: 26px;
  }
  .primary-filters {
    margin: 20px 0 10px;
    gap: 20px;
  }
  .primary-filters label {
    flex: 1;
    max-width: 260px;
  }
  .advanced-filters {
    border: 0;
    padding: 4px 0 18px;
  }
  .advanced-filters summary {
    font-size: 13px;
    color: var(--muted);
  }
  .result-count {
    padding: 20px 0;
    border-top: 1px solid var(--border);
  }
  @media (max-width: 640px) {
    h1 {
      font-size: 30px;
    }
    .search-heading {
      align-items: start;
      flex-direction: column;
      gap: 8px;
    }
    .primary-filters {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .primary-filters label {
      min-width: 0;
      max-width: none;
    }
    .primary-filters select {
      width: 100%;
    }
    .searchbox {
      font-size: 16px;
      padding: 12px;
    }
    .search-entry button {
      padding-inline: 14px;
    }
  }
</style>
