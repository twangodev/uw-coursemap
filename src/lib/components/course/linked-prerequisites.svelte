<script lang="ts">
  import {
    type Course,
    CourseUtils,
  } from "$lib/types/course.ts";
  import {
    HoverCard,
    HoverCardTrigger,
  } from "$lib/components/ui/hover-card/index.js";
  import HoverLinkedRequisiteContent from "./hover-linked-requisite-content.svelte";
  import ClampedParagraph from "$lib/components/clamped-paragraph.svelte";
  import { localizeHref } from "$lib/paraglide/runtime";

  interface Props {
    course: Course;
  }

  let { course }: Props = $props();

  let prerequisites = $derived(course.prerequisites);
  let linkedPrerequisites = $derived(prerequisites.linked_requisite_text);
</script>

<div>
  {#each linkedPrerequisites as item}
    {#if typeof item === "string"}
      {item}
    {:else if typeof item === "object"}
      <HoverCard>
        <HoverCardTrigger>
          <a
            href={localizeHref(`/courses/${CourseUtils.sanitizeCourseReferenceToString(item)}`)}
            class="underline-offset-2 hover:underline focus-visible:outline-2"
          >
            {CourseUtils.courseReferenceToString(item)}
          </a>
        </HoverCardTrigger>
        <HoverLinkedRequisiteContent courseReference={item} />
      </HoverCard>
    {/if}
  {/each}
</div>
