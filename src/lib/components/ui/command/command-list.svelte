<script lang="ts">
  import { Command as CommandPrimitive } from "bits-ui";
  import { cn } from "$lib/utils.js";

  let {
    ref = $bindable(null),
    class: className,
    ...restProps
  }: CommandPrimitive.ListProps = $props();
</script>

<CommandPrimitive.List
  class={cn("max-h-[300px] overflow-x-hidden overflow-y-auto", className)}
  {...restProps}
  bind:ref
/>
