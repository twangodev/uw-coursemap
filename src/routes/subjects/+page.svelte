<script lang="ts">
  import { onMount } from "svelte";
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import { api } from "$lib/api";

  let entries: [string, string][] = $state([]);

  onMount(async () => {
    const { data } = await api.GET("/subjects");
    if (data) {
      entries = Object.entries(data);
    }
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
