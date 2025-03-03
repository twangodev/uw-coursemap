<script lang="ts">
	import Search from "lucide-svelte/icons/search";
	import { cn } from "$lib/utils.js";
    import { Input } from "./ui/input";
	let className: string | undefined | null = undefined;
	export { className as class };
	export let value: string = "";
</script>

<div class="flex items-center border-b px-2" data-cmdk-input-wrapper="">
	<Search class="mr-2 h-4 w-4 shrink-0 opacity-50" />
	<Input
		class={cn(
			"placeholder:text-muted-foreground flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50 border-none focus-visible:ring-0 focus-visible:ring-opacity-0 focus-visible:ring-offset-0",
			className
		)}
		{...$$restProps}
		bind:value
	/>
</div>
