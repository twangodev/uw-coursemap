<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {page} from '$app/state';
    import {type Course, courseReferenceStringToCourse} from "$lib/types/course.ts";
    import {apiFetch} from "$lib/api.ts";
    import {getLatestTermIdPromise, type Terms} from "$lib/types/terms.ts";
    import {CourseHeader, CourseTabs} from "$lib/components/course";

    let courseIdentifier = $derived(page.params.courseIdentifier);

    let course: Promise<Course> = $derived(courseReferenceStringToCourse(courseIdentifier));

    let terms: Promise<Terms> = (async () => {
        let termsData = await apiFetch(`/terms.json`)
        return await termsData.json()
    })();

    let selectedTerm: string | undefined = $state(undefined)

    let latestTerm = $derived.by(async () => {
        selectedTerm = String(await getLatestTermIdPromise(terms))
        return selectedTerm
    });

</script>

<ContentWrapper>
    {#await Promise.all([course, terms, latestTerm])}
        <p class="text-center">Loading...</p>
    {:then [course, terms]}
        <CourseHeader
                course={course}
                terms={terms}
                bind:selectedTerm={selectedTerm}
        />
        <CourseTabs
                course={course}
                terms={terms}
                selectedTerm={selectedTerm}
        />
    {:catch error}
        <p class="text-red-600">Error loading course: {error.message}</p>
    {/await}
</ContentWrapper>