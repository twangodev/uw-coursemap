<script lang="ts">
    import { onMount } from "svelte";
    import {Button} from "$lib/components/ui/button";
    import {cn} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import CtrlCmd from "$lib/components/CtrlCmd.svelte";
    import { apiQueryFetch } from "$lib/api";
    import { writable } from "svelte/store";
    import CustomInput from "./CustomInput.svelte";

    export let wide = false;

    let open = false;

    $: searchQuery = "";
    let suggestions = writable<string[]>([]);
    $: updateSuggestions(searchQuery);

    async function updateSuggestions(query: string) {
        if (query.length <= 0) {
            $suggestions = []; 
            return
        }
        const response = await apiQueryFetch(searchQuery) 
        console.log(response);
        const data = await response.json()
        $suggestions = data.map((item: any) => item[0])
        console.log($suggestions);
    }

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
		"text-muted-foreground relative w-full justify-start text-sm sm:pr-12", wide ? "lg:w-[45rem] md:w-96" : "lg:w-80 md:w-40"
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
    <CustomInput placeholder="Search courses, programs..." bind:value={searchQuery} />
    <Command.List>
        <Command.Empty>No results found.</Command.Empty>
        <Command.Group heading="courses">
                  
            {#each $suggestions as suggestion, index }
                <Command.Item>{suggestion}</Command.Item>
            {/each}
        </Command.Group>
    </Command.List>
</Command.Dialog>
