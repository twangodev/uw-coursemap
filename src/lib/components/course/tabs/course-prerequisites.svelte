<script lang="ts">
  import {
    type Course,
    type CourseReference,
    CourseUtils,
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
  import { m } from "$lib/paraglide/messages";
  import { astToElements } from "$lib/components/cytoscape/cytoscape-init";
  import { takenCoursesStore } from "$lib/takenCoursesStore";

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

  const takenCourses = $derived($takenCoursesStore.map((course: CourseReference) => {
      return CourseUtils.courseReferenceToString(course);
  }));

  
  const elements = $derived(astToElements(
    course.prerequisites.abstract_syntax_tree,
    CourseUtils.courseReferenceToString(course.course_reference)
  ));

</script>

<Card class="flex h-[600px] flex-col">
  <CardHeader>
    <div class="flex items-center justify-between">
      <div>
        <CardTitle>{m["course.prerequisites.mapTitle"]()}</CardTitle>
        <CardDescription>
          {m["course.prerequisites.mapDescription"]()}
        </CardDescription>
        <CardDescription>
          {m["course.prerequisites.mapNote"]()}
        </CardDescription>
      </div>
      <Button
        class="flex items-center gap-2"
        href="/explorer/{course.course_reference
          .subjects[0]}?focus={CourseUtils.courseReferenceToSanitizedString(
          course.course_reference,
        )}"
        size="sm"
        variant="outline"
      >
        <BookOpen class="h-4 w-4" />
        {m["course.prerequisites.viewOnDepartmentGraph"]()}
      </Button>
    </div>
  </CardHeader>
  <CardContent class="flex-1">
    <div class="flex h-full w-full">
      {#key course}
        <Cytoscape
          elementDefinitions={elements}
          styleEntries={prerequisiteStyleEntries}
          allowFocusing={false}
        />
      {/key}
    </div>
  </CardContent>
</Card>
