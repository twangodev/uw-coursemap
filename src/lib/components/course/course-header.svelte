<script lang="ts">
  import { type Course, courseReferenceToString } from "$lib/types/course.js";
  import ContentH1 from "$lib/components/content/content-h1.svelte";
  import TermSelector from "$lib/components/term-selector.svelte";
  import type { Terms } from "$lib/types/terms.ts";

  interface Props {
    course: Course;
    terms: Terms;
    selectedTerm: string | undefined;
  }

  let { course, terms, selectedTerm }: Props = $props();
</script>

<div class="flex items-center justify-between">
  <div>
    <ContentH1>{course.course_title}</ContentH1>
    <div class="my-2 text-xl font-bold">
      {courseReferenceToString(course.course_reference)}
    </div>
  </div>
  <TermSelector {selectedTerm} {terms} />
</div>
