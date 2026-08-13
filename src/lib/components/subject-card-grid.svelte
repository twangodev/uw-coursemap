<script lang="ts">
  import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import { localizeHref } from "$lib/paraglide/runtime";

  interface Props {
    subjects: [string, string][];
  }

  let { subjects }: Props = $props();

  let sorted = $derived(
    [...subjects].sort(([, a], [, b]) => a.localeCompare(b)),
  );
</script>

<div
  class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
>
  {#each sorted as [code, name]}
    <a href={localizeHref(`/stats/${code}`)} class="flex h-full w-full">
      <Card class="flex h-full w-full flex-col">
        <CardHeader>
          <CardTitle class="truncate">{name}</CardTitle>
          <CardDescription class="truncate font-bold">
            {code}
          </CardDescription>
        </CardHeader>
      </Card>
    </a>
  {/each}
</div>
