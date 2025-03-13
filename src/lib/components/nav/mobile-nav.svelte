<script lang="ts">
    import { siteConfig } from "$lib/config/site.js";
    import * as Sheet from "$lib/components/ui/sheet";
    import {Button} from "$lib/components/ui/button";
    import MobileLink from "$lib/components/nav/mobile-link.svelte";
    import Crest from "$lib/components/Crest.svelte";
    import {navigation} from "$lib/config/navigation.ts";
    import {ScrollArea} from "$lib/components/ui/scroll-area";
    import {Menu} from "lucide-svelte";

    let open = $state(false);
</script>

<Sheet.Root bind:open>
    <Sheet.Trigger>
        <Button
                variant="ghost"
                class="mr-2 px-0 text-base hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 md:hidden"
        >
            <Menu/>
            <span class="sr-only">Toggle Menu</span>
        </Button>
    </Sheet.Trigger>
    <Sheet.Content side="left" class="pr-0">
        <MobileLink href="/" class="flex items-center" bind:open>
            <Crest/>
            <span class="font-bold">{siteConfig.name}</span>
        </MobileLink>
        <ScrollArea orientation="both" class="my-4 h-[calc(100vh-8rem)] pb-10 pl-6">
            <div class="flex flex-col space-y-3">
                {#each navigation as navItem}
                    {#if navItem.href}
                        <MobileLink href={navItem.href} bind:open class="text-foreground">
                            {navItem.title}
                        </MobileLink>
                    {/if}
                {/each}
            </div>
        </ScrollArea>
    </Sheet.Content>
</Sheet.Root>
