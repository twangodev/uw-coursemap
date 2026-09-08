<script lang="ts">
  import { courseCollections } from "$lib/course-collections";
  let {
    subject = "",
    term = "",
    active = "",
  }: { subject?: string; term?: string; active?: string } = $props();
  let query = $derived(
    new URLSearchParams({
      ...(term ? { term } : {}),
    }).toString(),
  );
</script>

<nav aria-label="Course collections" class="collections">
  {#each Object.entries(courseCollections) as [slug, collection]}
    <a
      href={`${subject ? `/subjects/${encodeURIComponent(subject)}` : "/courses"}/${slug}${query ? `?${query}` : ""}`}
      aria-current={active === slug ? "page" : undefined}
      >{collection.title}<span aria-hidden="true">↗</span></a
    >
  {/each}
</nav>

<style>
  .collections {
    display: flex;
    flex-wrap: wrap;
    gap: 14px 32px;
    margin: 12px 0 36px;
  }
  a {
    display: inline-flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-size: 15px;
  }
  a[aria-current="page"] {
    color: var(--accent);
    border-color: var(--accent);
  }
  span {
    color: var(--muted);
  }
</style>
