<script lang="ts">
  import { navigating } from "$app/state";
  import { LoaderCircle } from "@lucide/svelte";
  import { fade, fly } from "svelte/transition";
  import arrayShuffle from "array-shuffle";
  import loadingConfig from "$lib/config/loading-messages.json";
  
  // Declarative navigation state
  let isNavigating = $derived(!!navigating.to);
  
  // Loading messages from config
  const loadingMessages = loadingConfig.messages;
  
  let shuffledMessages = $state<string[]>([]);
  let messageIndex = $state(0);
  let currentMessage = $derived(shuffledMessages[messageIndex] || loadingMessages[0]);
  
  // Shuffle and cycle through messages when navigating
  $effect(() => {
    if (isNavigating) {
      shuffledMessages = arrayShuffle(loadingMessages);
      messageIndex = 0;
      
      const interval = setInterval(() => {
        messageIndex = (messageIndex + 1) % shuffledMessages.length;
      }, 1000);
      
      return () => clearInterval(interval);
    }
  });
</script>

{#if isNavigating}
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
    aria-hidden="false"
    aria-label="Loading page"
    transition:fade={{ duration: 200, delay: 150 }}
  >
    <div class="flex flex-col items-center gap-4">
      <LoaderCircle class="h-10 w-10 animate-spin text-primary" />
      <div class="relative h-6 w-64 overflow-hidden">
        {#key currentMessage}
          <span 
            class="absolute inset-0 text-center text-sm font-medium text-muted-foreground"
            in:fly={{ y: 20, duration: 300 }}
            out:fly={{ y: -20, duration: 300 }}
          >
            {currentMessage}
          </span>
        {/key}
      </div>
    </div>
  </div>
{/if}