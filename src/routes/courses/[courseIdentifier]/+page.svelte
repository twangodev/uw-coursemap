<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import { CourseHeader, CourseTabs } from "$lib/components/course";

  let { data } = $props();

  let terms = $derived(data.terms);
  let selectedTerm = $derived(data.selectedTermId);
  let course = $derived(data.course);
  let similarCourses = $derived(data.similarCourses);
  let instructors = $derived(data.instructors);
  let prerequisiteElementDefinitions = $derived(
    data.prerequisiteElementDefinitions,
  );
  let prerequisiteStyleEntries = $derived(data.prerequisiteStyleEntries);
</script>

<ContentWrapper>
  <CourseHeader {course} {selectedTerm} {terms} />
  <CourseTabs
    {course}
    {similarCourses}
    {instructors}
    {selectedTerm}
    {terms}
    {prerequisiteElementDefinitions}
    {prerequisiteStyleEntries}
  />
</ContentWrapper>
