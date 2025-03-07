<script lang="ts">
    import { cn } from "$lib/utils.js";

    interface Props {
        class?: string | undefined | null;
        children?: import('svelte').Snippet;
        [key: string]: any
    }

    let { class: className = undefined, children, ...rest }: Props = $props();
    
</script>

<section
        class={cn(
		"mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20",
		className
	)}
        {...rest}
>
    {@render children?.()}
</section>
