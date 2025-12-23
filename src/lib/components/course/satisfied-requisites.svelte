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
  import { localizeHref } from "$lib/paraglide/runtime";

  interface Props {
    course: Course;
  }

  let { course }: Props = $props();

  let requisites = $derived(course.satisfies);

  function intersperseWithAnd<T>(items: T[] | undefined): (T | string)[] {
    if (!items || items.length === 0) {
      return ["This course does not satisfy any prerequisites."];
    }

    const len = items.length;

    if (len === 1) {
      return [items[0]];
    }
    if (len === 2) {
      return [items[0], " and ", items[1]];
    }

    const result: (T | string)[] = [];
    for (let i = 0; i < len; i++) {
      if (i > 0) {
        result.push(i === len - 1 ? ", and " : ", ");
      }
      result.push(items[i]);
    }
    return result;
  }

  let linkedRequisites = $derived(intersperseWithAnd(requisites));
</script>

<div>
  {#each linkedRequisites as item}
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
