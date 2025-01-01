<script lang="ts">
    import {LucideMail} from "lucide-svelte";
    import {Avatar, AvatarFallback} from "$lib/components/ui/avatar";
    import type {FullInstructorInformation} from "$lib/types/instructor.ts";
    import * as Tooltip from "$lib/components/ui/tooltip";
    import ColoredNumberBox from "$lib/components/instructor-preview/ColoredNumberBox.svelte";

    export let instructor: FullInstructorInformation;
    export let showRating: boolean = false;
    export let showOtherDetails: boolean = false;

    let {name, email} = instructor;
    let averageRating = instructor?.data?.average_rating;
    let averageDifficulty = instructor?.data?.average_difficulty;
    let wouldTakeAgain = instructor?.data?.would_take_again_percent;

</script>

<a
        class="flex justify-between items-center p-2 rounded-lg hover:bg-muted transition-colors w-full"
        target="_blank"
        href="/instructors/{name.replaceAll(' ', '_').replaceAll('/', '_')}"
>
    <div class="flex items-center overflow-hidden">
        <Avatar class="flex-shrink-0">
            <AvatarFallback>{name[0]}</AvatarFallback>
        </Avatar>
        <div class="ml-4 flex-1 min-w-0">
            <h4 class="text-sm font-semibold truncate">{name}</h4>
            <div class="flex items-center py-1">
                <LucideMail class="mr-2 h-4 w-4 opacity-70 flex-shrink-0" />
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

