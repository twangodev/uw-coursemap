<!-- THIS IS NOT FROM SHADCN -->
<script lang="ts">
  import type { HTMLButtonAttributes } from "svelte/elements";
  import { cn } from "$lib/utils";
  import { X } from "@lucide/svelte";

  type $$Props = HTMLButtonAttributes;
  let className: $$Props["class"] = undefined;
  export { className as class };
</script>

<button
  class={cn(
    "ring-offset-background focus:ring-ring absolute top-2 right-2 rounded-md opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-none",
    className,
  )}
  {...$$restProps}
>
  <X class="h-4 w-4" />
  <span class="sr-only">Close</span>
</button>
