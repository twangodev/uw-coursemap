<script lang="ts">
  import type { Claim } from "$lib/types";
  import CitationPopover from "./CitationPopover.svelte";
  let { claims = [], reviewFiles = [], coursePath = "" }: { claims: Claim[]; reviewFiles?: string[]; coursePath?: string } = $props();
</script>

<div class="stack">
  {#each claims as claim}<div class="claim">
      <p>{claim.text}{#if claim.citations?.length}<CitationPopover citations={claim.citations} {reviewFiles} {coursePath} />{/if}</p>
    </div>{/each}
</div>
