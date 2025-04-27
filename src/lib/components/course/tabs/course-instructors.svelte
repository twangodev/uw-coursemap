<script lang="ts">
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
    import {ArrowUpRight} from "@lucide/svelte";
    import type {FullInstructorInformation} from "$lib/types/instructor.ts";

    interface Props {
        instructors: Promise<FullInstructorInformation[]>;
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
        {#await instructors}
            {$inspect(instructors)}
            <p class="text-center">Loading...</p>
        {:then instructors}
            {#if instructors.length === 0}
            No instructors found.
            {/if}
            {#each instructors as instructor}
                <InstructorPreview
                        {instructor}
                        showRating={true}
                        showOtherDetails={true}
                />
            {/each}
        {:catch error}
            <p class="text-red-600">Error loading instructors: {error.message}</p>
        {/await}
    </CardContent>
</Card>
{#await instructors}
    <Card>
        <CardContent>
            <p class="text-center">Loading...</p>
        </CardContent>
    </Card>
{:then instructors}
    {#if instructors.length > 0}
    <Card>

        <CardContent>
            <InstructorWordCloud instructors={instructors}/>
            
        </CardContent>
    </Card>
    {/if}
{:catch error}
    <Card>
        <CardContent>
            <p class="text-red-600">Error loading instructors: {error.message}</p>
        </CardContent>
    </Card>
{/await}