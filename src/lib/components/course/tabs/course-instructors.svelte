<script lang="ts">
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
  import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
  import { ArrowUpRight } from "@lucide/svelte";
  import type { FullInstructorInformation } from "$lib/types/instructor.ts";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    instructors: FullInstructorInformation[];
  }

  let { instructors }: Props = $props();

  let showMax = $state(6);
  let safeShowMax = $derived(Math.min(showMax, instructors.length));

  function showMore() {
    showMax += 3;
  }

  $effect(() => {
    if (instructors) {
      showMax = 6;
    }
  });
</script>

<Card>
  <CardHeader>
    <CardTitle>{m["course.instructors.title"]()}</CardTitle>
    <CardDescription class="flex">
      {m["course.overview.sortedByRatings"]()}
      <a
        class="ml-1 flex items-center font-medium underline-offset-4 hover:underline"
        href="https://www.ratemyprofessors.com/"
        target="_blank"
      >
        {m["course.overview.rateMyProfessors"]()}
        <ArrowUpRight class="inline h-4 w-4" />
      </a>
    </CardDescription>
  </CardHeader>
  <CardContent>
    {#if instructors.length === 0}
      <p class="text-center">{m["course.instructors.noInstructorsFound"]()}</p>
    {/if}
    {#key instructors}
      {#each instructors.slice(0, safeShowMax) as instructor}
        <InstructorPreview
          {instructor}
          showRating={true}
          showOtherDetails={true}
        />
      {/each}
    {/key}
    {#if showMax < instructors.length}
      <div class="text-muted-foreground flex justify-center text-sm">
        <button
          class="text-center hover:cursor-pointer hover:underline"
          onclick={showMore}
        >
          {m["course.instructors.showMore"]({ count: instructors.length - showMax })}
        </button>
        <span class="px-1">{m["course.instructors.or"]()}</span>
        <button
          class="text-center hover:cursor-pointer hover:underline"
          onclick={() => (showMax = instructors.length)}
        >
          {m["course.instructors.showAll"]()}
        </button>
      </div>
    {/if}
  </CardContent>
</Card>
{#if instructors.length > 0}
  <Card>
    <CardContent>
      <InstructorWordCloud {instructors} />
    </CardContent>
  </Card>
{/if}
