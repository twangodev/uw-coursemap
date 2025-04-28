<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {CourseHeader, CourseTabs} from "$lib/components/course";
    import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";
    import {onMount, tick} from "svelte";

    let {data} = $props();

    let terms = $derived(data.terms);
    let selectedTerm = $derived(data.selectedTermId);
    let course = $derived(data.course);
    let instructors: FullInstructorInformation[] = $state([]);

    $effect(() => {
        (async () => {
            instructors = await getFullInstructorInformation(course, terms, selectedTerm, fetch);
        })();
    })

</script>

<ContentWrapper>
    <CourseHeader {course} bind:selectedTerm={selectedTerm} {terms}/>
    <CourseTabs {course} {instructors} {selectedTerm} {terms}/>
</ContentWrapper>