<script lang="ts">
    import { onMount } from "svelte";
    import {Button} from "$lib/components/ui/button";
    import {cn} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import CtrlCmd from "$lib/components/CtrlCmd.svelte";

    let open = false;

    onMount(() => {
        function handleKeydown(e: KeyboardEvent) {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                open = true;
            }
        }
        document.addEventListener("keydown", handleKeydown);

        return () => {
            document.removeEventListener("keydown", handleKeydown);
        };
    });
</script>

<Button
        variant="outline"
        class={cn(
		"text-muted-foreground relative w-full justify-start text-sm sm:pr-12 md:w-40 lg:w-80"
	)}
        on:click={() => (open = true)}
        {...$$restProps}
>
    <span class="hidden lg:inline-flex">Search courses, programs... </span>
    <span class="inline-flex lg:hidden">Search...</span>
    <kbd
            class="bg-muted pointer-events-none absolute right-1.5 top-2 hidden h-5 select-none items-center gap-1 rounded border px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex"
    >
        <CtrlCmd />K
    </kbd>
</Button>
<Command.Dialog bind:open>
    <Command.Input placeholder="Search courses, programs..." />
    <Command.List>
        <Command.Empty>No results found.</Command.Empty>
    </Command.List>
</Command.Dialog>
