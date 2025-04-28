<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {CourseHeader, CourseTabs} from "$lib/components/course";

    let {data} = $props();

    let terms = $derived(data.terms);
    let selectedTerm = $derived(data.selectedTermId);
    let course = $derived(data.course);
    let instructors = $derived(data.instructors);

</script>

<ContentWrapper>
    <CourseHeader {course} {selectedTerm} {terms}/>
    <CourseTabs {course} {instructors} {selectedTerm} {terms}/>
</ContentWrapper>