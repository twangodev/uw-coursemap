<script lang="ts">
    import {cn} from "$lib/utils.js";

    interface Props {
        class?: string | undefined | null;
        children?: import('svelte').Snippet;
        [key: string]: any
    }

    let { class: className = undefined, children, ...rest }: Props = $props();
    
</script>

<h1
        class={cn(
		"text-center text-3xl font-bold leading-tight tracking-tighter md:text-6xl lg:leading-[1.1]",
		className
	)}
        {...rest}
>
    {@render children?.()}
</h1>
