<script lang="ts">
  import { onMount } from "svelte";
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import { apiFetch } from "$lib/api.ts";

  let entries: [string, string][] = $state([]);

  onMount(async () => {
    const response = await apiFetch(`/subjects.json`);
    let majors = await response.json();

    entries = Object.entries(majors);
  });
</script>

<ContentWrapper>
  <h1 class="mb-6 text-xl font-semibold">List of Subjects</h1>

  <ul class="space-y-2">
    {#each entries as [abbr, full]}
      <li
        class="text-muted-foreground hover:text-foreground text-sm transition-colors"
      >
        <a
          href={`/explorer/${abbr}`}
          class="text-muted-foreground hover:text-foreground transition-colors"
        >
          {abbr} - {full}
        </a>
      </li>
    {/each}
  </ul>
</ContentWrapper>
