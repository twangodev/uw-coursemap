<script lang="ts">
  import {
    type Course,
    sanitizeCourseToReferenceString,
  } from "$lib/types/course.js";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
  import { BookOpen } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import type { ElementDefinition } from "cytoscape";
  import type { StyleEntry } from "$lib/components/cytoscape/graph-styles.ts";

  interface Props {
    course: Course;
    prerequisiteElementDefinitions: ElementDefinition[];
    prerequisiteStyleEntries: StyleEntry[];
  }

  let {
    course,
    prerequisiteElementDefinitions,
    prerequisiteStyleEntries,
  }: Props = $props();
</script>

<Card class="flex h-[600px] flex-col">
  <CardHeader>
    <div class="flex items-center justify-between">
      <div>
        <CardTitle>Course Prerequisites Map</CardTitle>
        <CardDescription>
          Visual representation of course prerequisites and related courses.
        </CardDescription>
        <CardDescription>
          Note: We aren't showing all possible requisite relationships, only
          those that are directly relevant to the course.
        </CardDescription>
      </div>
      <Button
        class="flex items-center gap-2"
        href="/explorer/{course.course_reference
          .subjects[0]}?focus={sanitizeCourseToReferenceString(
          course.course_reference,
        )}"
        size="sm"
        variant="outline"
      >
        <BookOpen class="h-4 w-4" />
        View on Department Graph
      </Button>
    </div>
  </CardHeader>
  <CardContent class="flex-1">
    <div class="flex h-full w-full">
      {#key course}
        <Cytoscape
          elementDefinitions={prerequisiteElementDefinitions}
          styleEntries={prerequisiteStyleEntries}
          filter={course}
          allowFocusing={false}
        />
      {/key}
    </div>
  </CardContent>
</Card>
