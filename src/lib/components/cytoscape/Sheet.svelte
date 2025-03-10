<script lang="ts">
    import {Root, SheetContent, SheetDescription, SheetHeader, SheetTitle} from "$lib/components/ui/sheet";
    import {Skeleton} from "$lib/components/ui/skeleton";
    import {ScrollArea} from "$lib/components/ui/scroll-area";
    import {courseReferenceToString, sanitizeCourseToReferenceString, type Course} from "$lib/types/course.ts";
    import {Separator} from "$lib/components/ui/separator";
    import {Button} from "$lib/components/ui/button";
    import InstructorPreview from "../instructor-preview/InstructorPreview.svelte";
    import { ArrowUpRight } from "lucide-svelte";
    
    interface Props {
        sheetOpen: boolean;
        selectedCourse: Course | null;
    }
    let { sheetOpen = $bindable<boolean>(), selectedCourse }: Props = $props();
</script>

<Root bind:open={sheetOpen}>
    <SheetContent class="flex flex-col h-full">
        <SheetHeader class="sticky">
            <SheetTitle class="text-2xl">
                {#if selectedCourse}
                    {courseReferenceToString(selectedCourse.course_reference)}
                {:else}
                    <Skeleton class="h-6 w-9/12"/>
                {/if}
            </SheetTitle>
        </SheetHeader>
        <ScrollArea class="flex-1 overflow-y-auto mr-1">
            <div class="font-semibold">
                {#if selectedCourse}
                    {selectedCourse.course_title}
                {:else}
                    <Skeleton class="h-5 w-6/12"/>
                {/if}
            </div>
            <Separator class="my-1"/>
            <SheetDescription>
                {#if selectedCourse}
                    {selectedCourse.description}
                {:else}
                    <Skeleton class="h-5 w-6/12"/>
                {/if}
            </SheetDescription>
            {#if selectedCourse}
                {#each Object.entries(selectedCourse?.enrollment_data?.instructors ?? {}) as [name, email], index}
                    {#if index === 0}
                        <div class="font-semibold mt-2">INSTRUCTORS</div>
                        <Separator class="my-1" />
                    {/if}
                    <InstructorPreview instructor={{
                        name: name,
                        email: email,
                        credentials: null,
                        rmp_data: null,
                        department: null,
                        official_name: null,
                        position: null
                    }}/>
                {/each}
            {/if}
        </ScrollArea>
        {#if selectedCourse}
            <Button class="sticky bottom-0" href="/courses/{sanitizeCourseToReferenceString(selectedCourse.course_reference)}" target="_blank">
                View Course Page
                <ArrowUpRight class="h-4 w-4"/>
            </Button>
        {/if}
    </SheetContent>
</Root>
