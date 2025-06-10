<script lang="ts">
  import { HoverCardContent } from "$lib/components/ui/hover-card";
  import {
    type Course,
    type CourseReference,
    courseReferenceToCourse,
    courseReferenceToString,
    getLatestInstructorNames,
  } from "$lib/types/course.ts";
  import { Users } from "@lucide/svelte";
  import { Skeleton } from "$lib/components/ui/skeleton";
  import { onMount } from "svelte";

  interface Props {
    courseReference: CourseReference;
  }

  let { courseReference }: Props = $props();

  let course = $state<Course | null>(null);

  onMount(async () => {
    course = await courseReferenceToCourse(courseReference);
  });
</script>

<HoverCardContent>
  <div>
    <h4 class="line-clamp-1 text-sm font-semibold">
      {courseReferenceToString(courseReference)}
    </h4>
    {#if course}
      <h5 class="line-clamp-1 pt-0.5 text-xs">{course.course_title}</h5>
      <p class="line-clamp-2 pt-1 text-xs">{course.description}</p>
      <div class="flex items-center pt-2">
        <Users class="mr-2 size-3" />
        <span class="text-muted-foreground line-clamp-1 text-xs"
          >{getLatestInstructorNames(course).join(", ")}</span
        >
      </div>
    {:else}
      <div class="space-y-1">
        <Skeleton class="h-4 w-1/2 rounded" />
        <Skeleton class="h-3 w-full rounded" />
        <Skeleton class="h-3 w-5/6 rounded" />
        <div class="flex items-center space-x-2 pt-2">
          <Skeleton class="h-4 w-4 rounded-full" />
          <Skeleton class="h-3 w-1/3 rounded" />
        </div>
      </div>
    {/if}
  </div>
</HoverCardContent>
