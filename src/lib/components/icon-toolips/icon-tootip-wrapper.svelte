<script lang="ts">
  import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
  } from "$lib/components/ui/tooltip/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import type { Snippet } from 'svelte';

  interface Props {
    tooltip: string;
    onclick: () => void;
    children: Snippet;
  }

  let { tooltip, onclick, children }: Props = $props();
</script>

<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>
      <Button {onclick} size="sm" variant="outline" class="h-8 w-8 px-0">
        {@render children?.()}
      </Button>
    </TooltipTrigger>
    <TooltipContent>{tooltip}</TooltipContent>
  </Tooltip>
</TooltipProvider>
