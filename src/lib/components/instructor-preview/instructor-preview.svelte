<script lang="ts">
    import {LucideMail} from "@lucide/svelte";
    import {Avatar, AvatarFallback} from "$lib/components/ui/avatar";
    import type {FullInstructorInformation} from "$lib/types/instructor.ts";
    import ColoredNumberBox from "$lib/components/instructor-preview/colored-number-box.svelte";
    import {slide, type SlideParams} from "svelte/transition";
    import {slideParams} from "$lib/transitions.ts";

    interface Props {
        instructor: FullInstructorInformation,
        showRating?: boolean,
        showOtherDetails?: boolean,
        disableSlideOut?: boolean
    }

    let {
        instructor,
        showRating = false,
        showOtherDetails = false,
        disableSlideOut = false
    }: Props = $props();

    let {name, email} = instructor;
    let averageRating = instructor?.rmp_data?.average_rating;
    let averageDifficulty = instructor?.rmp_data?.average_difficulty;
    let wouldTakeAgain = instructor?.rmp_data?.would_take_again_percent;

    const slideOutParams: SlideParams = {
        ...slideParams,
        duration: disableSlideOut ? 0 : slideParams.duration
    }

</script>

<div in:slide|global={slideParams} out:slide|global={slideOutParams}>
    <a
        class="flex justify-between items-center p-2 rounded-lg hover:bg-muted transition-colors w-full"
        target="_blank"
        href="/instructors/{name.replaceAll(' ', '_').replaceAll('/', '_')}"
    >
        <div class="flex items-center overflow-hidden">
            <Avatar class="shrink-0">
                <AvatarFallback>{name[0]}</AvatarFallback>
            </Avatar>
            <div class="ml-4 flex-1 min-w-0">
                <h4 class="text-sm font-semibold truncate">{name}</h4>
                <div class="flex items-center py-1">
                    <LucideMail class="mr-2 h-4 w-4 opacity-70 shrink-0" />
                    <span class="text-muted-foreground text-xs underline-offset-2 truncate">{email}</span>
                </div>
            </div>
        </div>
        <div class="flex gap-4 items-center">
            {#if showRating}
                <ColoredNumberBox amount={averageRating} description="Rating" scale={5} />
            {/if}
            {#if showOtherDetails}
                <ColoredNumberBox amount={averageDifficulty} description="Difficulty" scale={5} invert={true}/>
                <ColoredNumberBox amount={wouldTakeAgain} description="Take Again" scale={100}/>
            {/if}
        </div>
    </a>
</div>