<script lang="ts">
  import { LucideMail } from "@lucide/svelte";
  import { Avatar, AvatarFallback } from "$lib/components/ui/avatar";
  import { type FullInstructor, sanitizeInstructorId } from "$lib/types/instructor.ts";
  import ColoredNumberBox from "$lib/components/instructor-preview/colored-number-box.svelte";
  import { slide } from "svelte/transition";
  import { slideParams } from "$lib/transitions.ts";
  import { Badge } from "$lib/components/ui/badge";
  import { localizeHref } from "$lib/paraglide/runtime";

  interface Props {
    instructor: FullInstructor;
    showRating?: boolean;
    showOtherDetails?: boolean;
    rank?: number;
  }

  let {
    instructor,
    showRating = false,
    showOtherDetails = false,
    rank = undefined,
  }: Props = $props();

  let { name, email } = instructor;
  let averageRating = instructor?.rmp_data?.average_rating;
  let averageDifficulty = instructor?.rmp_data?.average_difficulty;
  let wouldTakeAgain = instructor?.rmp_data?.would_take_again_percent;
</script>

<div in:slide|global={slideParams}>
  <a
    class="hover:bg-muted flex items-center justify-between rounded-lg p-2 transition-colors"
    target="_blank"
    href={localizeHref(`/instructors/${sanitizeInstructorId(name)}`)}
  >
    <div class="flex items-center overflow-hidden">
      {#if rank}
        <Badge class="text-muted-foreground mr-2 text-xs" variant="outline"
          >#{rank}</Badge
        >
      {/if}
      <Avatar class="shrink-0">
        <AvatarFallback>{name[0]}</AvatarFallback>
      </Avatar>
      <div class="ml-4 min-w-0 flex-1">
        <h4 class="truncate text-sm font-semibold">{name}</h4>
        <div class="flex items-center py-1">
          <LucideMail class="mr-2 h-4 w-4 shrink-0 opacity-70" />
          <span
            class="text-muted-foreground truncate text-xs underline-offset-2"
            >{email}</span
          >
        </div>
      </div>
    </div>
    <div class="flex items-center gap-4">
      {#if showRating}
        <ColoredNumberBox
          amount={averageRating}
          description="Rating"
          scale={5}
        />
      {/if}
      {#if showOtherDetails}
        <ColoredNumberBox
          amount={averageDifficulty}
          description="Difficulty"
          scale={5}
          invert={true}
        />
        <ColoredNumberBox
          amount={wouldTakeAgain}
          description="Take Again"
          scale={100}
        />
      {/if}
    </div>
  </a>
</div>
