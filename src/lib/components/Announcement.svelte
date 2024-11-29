<script lang="ts">
    import Blocks from "lucide-svelte/icons/blocks";
    import { cn } from "$lib/utils.js";
    import {ArrowRight} from "lucide-svelte";
    import {Separator} from "$lib/components/ui/separator";

    let className: string | undefined | null = undefined;
    export { className as class };
</script>

<a
        href="https://www.ratemyprofessors.com/"
        target="_blank"
        class={cn(
		"bg-muted inline-flex items-center rounded-lg px-3 py-1 text-sm font-medium",
		className
	)}
        {...$$restProps}
>
    <Blocks class="size-4" />
    <Separator class="mx-2 h-4" orientation="vertical" />
    <span>Introducing Rate My Professor Statistics!</span>
    <ArrowRight class="ml-1 size-4" />
</a>
