<script lang="ts">
    import {cn} from "$lib/utils.js";
    import {ArrowRight} from "@lucide/svelte";
    import {Separator} from "$lib/components/ui/separator";

    interface Props {
        class?: string | undefined | null;
        [key: string]: any
    }

    let { class: className = undefined, ...rest }: Props = $props();
    
</script>

<a
        href="https://github.com/twangodev/uw-coursemap"
        target="_blank"
        class={cn(
		"bg-muted inline-flex items-center rounded-lg px-3 py-1 text-sm font-medium",
		className
	)}
        {...rest}
>
    <Blocks class="size-4" />
    <Separator class="mx-2 h-4" orientation="vertical" />
    <span>Drop a star on Github if this helped you!</span>
    <ArrowRight class="ml-1 size-4" />
</a>
