<script lang="ts">
    import { cn } from "$lib/utils.js";


    interface Props {
        balanced?: boolean;
        class?: string | undefined | null;
        children?: import('svelte').Snippet;
        [key: string]: any
    }

    let { balanced = true, class: className = undefined, children, ...rest }: Props = $props();
    
</script>

<p
        class={cn(
		"mx-auto text-muted-foreground max-w-[750px] text-center text-lg sm:text-xl",
		balanced && "text-balance",
		className
	)}
        {...rest}
>
    {@render children?.()}
</p>
