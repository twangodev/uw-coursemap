<script lang="ts">
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
    import {ArrowUpRight} from "@lucide/svelte";
    import type {FullInstructorInformation} from "$lib/types/instructor.ts";

    interface Props {
        instructors: FullInstructorInformation[];
    }

    let {instructors}: Props = $props();

</script>

<Card>
    <CardHeader>
        <CardTitle>Instructors</CardTitle>
        <CardDescription class="flex">
            Sorted by ratings from
            <a class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
               href="https://www.ratemyprofessors.com/"
               target="_blank"
            >
                Rate My Professors
                <ArrowUpRight class="h-4 w-4 inline"/>
            </a>
        </CardDescription>
    </CardHeader>
    <CardContent>
        {#if instructors.length === 0}
            <p class="text-center">No instructors found.</p>
        {/if}
        {#key instructors}
            {#each instructors as instructor}
                <InstructorPreview
                        {instructor}
                        showRating={true}
                        showOtherDetails={true}
                />
            {/each}
        {/key}
    </CardContent>
</Card>
{#if instructors.length > 0}
    <Card>
        <CardContent>
            <InstructorWordCloud instructors={instructors}/>
        </CardContent>
    </Card>
{/if}