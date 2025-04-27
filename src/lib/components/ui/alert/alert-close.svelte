<!-- THIS IS NOT FROM SHADCN -->
<script lang="ts">
    import type {HTMLButtonAttributes} from "svelte/elements";
    import {cn} from "$lib/utils";
    import {X} from "@lucide/svelte";

    type $$Props = HTMLButtonAttributes;
    let className: $$Props["class"] = undefined;
    export { className as class };
</script>

<button
    class={cn(
        "absolute right-2 top-2 rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        className
    )}
    {...$$restProps}
>
    <X class="h-4 w-4" />
    <span class="sr-only">Close</span>
</button>