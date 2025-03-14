<script lang="ts">

    import {Popover, PopoverContent, Trigger} from "$lib/components/ui/popover";
    import {Button} from "$lib/components/ui/button";
    import {ChevronsUpDown} from "lucide-svelte";
    import {Command, CommandItem} from "$lib/components/ui/command";
    import {CommandEmpty, CommandGroup} from "$lib/components/ui/command/index.js";
    import {tick} from "svelte";
    import Check from "lucide-svelte/icons/check";
    import {cn} from "$lib/utils.ts";

    interface Props {
        selectedTerm: string | null;
        terms: string[];
    }

    let {
        selectedTerm = $bindable(null),
        terms,
    }: Props = $props();

    let open = $state(false)
    let triggerRef = $state<HTMLButtonElement>(null!);

    function closeAndFocusTrigger() {
        open = false;
        tick().then(() => {
            triggerRef.focus();
        });
    }

</script>

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
                {selectedTerm || "Select a term..."}
                <ChevronsUpDown class="ml-2 size-4 shrink-0 opacity-50" />
            </Button>
        {/snippet}
    </Trigger>
    <PopoverContent>
        <Command>
            <CommandEmpty>No term found.</CommandEmpty>
            <CommandGroup>
                {#each terms as term}
                    <CommandItem
                        value={term}
                        onSelect={() => {
                            selectedTerm = term;
                            closeAndFocusTrigger();
                        }}
                    >
                        <Check
                                class={cn(selectedTerm !== term && "text-transparent")}
                        />
                        {term}
                    </CommandItem>
                {/each}
            </CommandGroup>
        </Command>
    </PopoverContent>
</Popover>