<script lang="ts">
    import {cn} from "$lib/utils.js";

    interface Props {
        class?: string | undefined | null;
        children?: import('svelte').Snippet;
    }

    let { class: className = undefined, children }: Props = $props();
    
</script>

<div class={cn("flex w-full items-center justify-center space-x-4 py-4 md:pb-10", className)}>
    {@render children?.()}
</div>
