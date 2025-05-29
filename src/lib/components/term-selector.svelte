<script lang="ts">

    import {Popover, PopoverContent, Trigger} from "$lib/components/ui/popover";
    import {Button} from "$lib/components/ui/button";
    import {ChevronsUpDown, Check, ChevronLeft, ChevronRight} from "@lucide/svelte";
    import {Command, CommandItem, CommandList} from "$lib/components/ui/command";
    import {CommandEmpty, CommandGroup, CommandInput} from "$lib/components/ui/command/index.js";
    import {cn} from "$lib/utils.ts";
    import {getLatestTermId, type Terms} from "$lib/types/terms.ts";
    import {goto} from "$app/navigation";
    import {tick} from "svelte";

    interface Props {
        selectedTerm: string | undefined;
        terms: Terms;
    }

    let {
        selectedTerm,
        terms,
    }: Props = $props();

    let open = $state(false)
    let triggerRef = $state<HTMLButtonElement>(null!);
    let latestTerm = $derived(getLatestTermId(terms));

    function closeAndFocusTrigger() {
        open = false;
        triggerRef.focus();
    }

    async function navigateTo(termId: string) {
        goto(`?term=${termId}`);
        await tick();
        closeAndFocusTrigger();
    }

    let previousTermId = $derived.by(() => {
        if (!selectedTerm) return undefined;
        const termIds = Object.keys(terms);

        const currentIndex = termIds.indexOf(selectedTerm);
        if (currentIndex > 0) {
            return termIds[currentIndex - 1];
        }
        return undefined;
    });

    let nextTermId = $derived.by(() => {
        if (!selectedTerm) return undefined;
        const termIds = Object.keys(terms);

        const currentIndex = termIds.indexOf(selectedTerm);
        if (currentIndex < termIds.length - 1) {
            return termIds[currentIndex + 1];
        }
        return undefined;
    });

</script>

<div class="flex items-center gap-2">

    <div class="hidden sm:inline-flex ">
        <Button
                variant="outline"
                onclick={() => previousTermId && navigateTo(previousTermId)}
                disabled={!previousTermId}
                aria-label="Previous term"
                size="icon"
                class="rounded-none rounded-l-md"
        >
            <ChevronLeft />
        </Button>

        <Button
                variant="outline"
                onclick={() => nextTermId && navigateTo(nextTermId)}
                disabled={!nextTermId}
                aria-label="Next term"
                size="icon"
                class="-ml-px rounded-none rounded-r-md"
        >
            <ChevronRight />
        </Button>
    </div>


    <Popover>
        <Trigger bind:ref={triggerRef}>
            {#snippet child({ props })}
                <Button
                        variant="outline"
                        class="w-[200px] justify-between"
                        {...props}
                        role="combobox"
                        aria-expanded={open}
                >
                    {selectedTerm ? terms[selectedTerm] : "Select a term..."}
                    <ChevronsUpDown class="ml-2 size-4 shrink-0 opacity-50" />
                </Button>
            {/snippet}
        </Trigger>
        <PopoverContent class="w-[200px] p-0">
            <Command>
                <CommandInput placeholder="Search term..."/>
                <CommandList>
                    <CommandEmpty>No term found.</CommandEmpty>
                    <CommandGroup>
                        {#each Object.entries(terms).toReversed() as [termId, termName]}
                            <CommandItem
                                value={termName}
                                onSelect={() => navigateTo(termId)}
                            >
                                <Check
                                    class={cn(selectedTerm !== termId && "text-transparent")}
                                />
                                {#if termId === latestTerm}
                                    Latest ({termName})
                                {:else}
                                    {termName}
                                {/if}
                            </CommandItem>
                        {/each}
                    </CommandGroup>
                </CommandList>
            </Command>
        </PopoverContent>
    </Popover>

</div>