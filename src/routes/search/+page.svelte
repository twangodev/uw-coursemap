<script lang="ts">
  import { Search } from "@lucide/svelte";
  import CourseCollections from "$lib/components/CourseCollections.svelte";
  import CourseFinder from "$lib/components/CourseFinder.svelte";
  import { instructorUrl, termName } from "$lib/format";
  let { data } = $props();
  function pageLink(n: number) {
    const q = new URLSearchParams({ ...data.results.filters, page: String(n) });
    return `/search?${q}`;
  }
</script>

<svelte:head
  ><title
    >{data.results.kind === "course" ? "Find courses" : "Find a professor"} · UW Courses</title
  ><meta name="robots" content="noindex,follow" /></svelte:head
>
<div class="search-heading">
  <h1>
    {data.results.kind === "course" ? "Explore courses" : "Find a professor"}
  </h1>
  <span>{termName(data.status.term)}</span>
</div>
{#if data.results.kind === "course"}
  <CourseCollections />
  <CourseFinder results={data.results} status={data.status} />
  <p class="switch">
    <a href="/search?kind=instructor">Looking for a professor? →</a>
  </p>
{:else}
  <form action="/search" class="instructor-search">
    <input type="hidden" name="kind" value="instructor" /><input
      name="q"
      aria-label="Search instructors"
      placeholder="A professor’s name…"
      value={data.results.q}
    /><button class="search-submit" aria-label="Search"><Search size={19} strokeWidth={1.5} /></button>
  </form>
  <p class="muted">{data.results.total} instructors</p>
  {#each data.results.items as i}<a
      class="course-row"
      href={instructorUrl(i.instructor_uid)}
      ><span>{i.name || "Name unavailable"}</span><span class="muted"
        >{#if i.bayesian_quality != null}{i.bayesian_quality.toFixed(1)}/5 adjusted · {/if}{i.current
          ? `Teaching in ${termName(data.status.term)}`
          : "Historical instructor"}</span
      ></a
    >{:else}<p class="empty">No instructors match this search.</p>{/each}
  <nav aria-label="Results pages">
    {#if data.results.page > 1}<a href={pageLink(data.results.page - 1)}
        >← Previous</a
      >{/if}{#if data.results.page * 30 < data.results.total}<a
        href={pageLink(data.results.page + 1)}>Next →</a
      >{/if}
  </nav>
  <p class="switch"><a href="/search">Find courses →</a></p>
{/if}

<style>
  .search-submit { display: grid; place-items: center; padding: 8px 10px; border: 0; background: transparent; }
  .search-heading {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 24px;
    margin: 16px 0 40px;
  }
  .search-heading h1 {
    font-size: 38px;
    font-weight: 500;
  }
  .search-heading span {
    font-size: 12px;
    color: var(--muted);
  }
  .switch {
    margin-top: 32px;
    font-size: 13px;
  }
  .instructor-search {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
  }
  .instructor-search input {
    flex: 1;
    min-width: 0;
    padding: 12px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font: inherit;
  }
  nav {
    display: flex;
    gap: 24px;
    margin-top: 24px;
  }
  @media (max-width: 600px) {
    .search-heading {
      flex-direction: column;
      gap: 8px;
    }
  }
</style>
