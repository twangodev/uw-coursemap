<script lang="ts">
  import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
  } from "$lib/components/ui/tooltip";
  import { Button } from "$lib/components/ui/button";

  interface Props {
    active: () => any;
    inactive: () => any;
    onclick: () => void;
    state: boolean;
    activeTooltip: string;
    inactiveTooltip: string;
  }

  let {
    active,
    inactive,
    onclick,
    state,
    activeTooltip,
    inactiveTooltip,
    ...restProps
  }: Props = $props();
</script>

<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>
      <Button
        {onclick}
        size="sm"
        variant="outline"
        class="h-8 w-8 px-0"
        {...restProps}
      >
        {#if state}
          {@render active()}
        {:else}
          {@render inactive()}
        {/if}
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      {#if state}
        {activeTooltip}
      {:else}
        {inactiveTooltip}
      {/if}
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
