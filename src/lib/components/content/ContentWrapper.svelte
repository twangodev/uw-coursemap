<script lang="ts">
    import {cn} from "$lib/utils.js";
    import type {WithElementRef} from "bits-ui";
    import type {HTMLAttributes} from "svelte/elements";

    let {
        ref = $bindable(null),
        class: className,
        children,
    }: WithElementRef<HTMLAttributes<HTMLDivElement>> = $props();
</script>

<div bind:this={ref} class={cn("container px-6 md:px-8 py-8", className)}>
    {@render children?.()}
</div>