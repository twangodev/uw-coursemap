<script lang="ts">
    import { resetMode, setMode } from "mode-watcher";
    import {Moon, Sun} from "@lucide/svelte";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import {Button} from "$lib/components/ui/button";

</script>

<DropdownMenu.Root>
    <DropdownMenu.Trigger >
        <Button variant="ghost" class="h-8 w-8 px-0">
            <Sun
                    class="dark:-roate-90 h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:scale-0"
            />
            <Moon
                    class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
            />
            <span class="sr-only">Toggle theme</span>
        </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="end">
        <DropdownMenu.Item onclick={() => setMode("light")}>Light</DropdownMenu.Item>
        <DropdownMenu.Item onclick={() => setMode("dark")}>Dark</DropdownMenu.Item>
        <DropdownMenu.Item onclick={() => resetMode()}>System</DropdownMenu.Item>
    </DropdownMenu.Content>
</DropdownMenu.Root>
