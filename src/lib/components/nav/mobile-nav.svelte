<script lang="ts">
  import * as Sheet from "$lib/components/ui/sheet";
  import { Button } from "$lib/components/ui/button";
  import MobileLink from "$lib/components/nav/mobile-link.svelte";
  import Logo from "$lib/components/logo.svelte";
  import { navigation } from "$lib/config/navigation.ts";
  import { ScrollArea } from "$lib/components/ui/scroll-area";
  import { Menu } from "@lucide/svelte";
  import LanguagePicker from "$lib/components/language-picker.svelte";
  import ModeToggle from "$lib/components/mode-toggle.svelte";
  import { m } from "$lib/paraglide/messages";

  let open = $state(false);
</script>

<Sheet.Root bind:open>
  <Sheet.Trigger>
    <Button
      variant="ghost"
      class="mr-2 px-0 text-base hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 md:hidden"
    >
      <Menu />
      <span class="sr-only">{m["nav.toggleMenu"]()}</span>
    </Button>
  </Sheet.Trigger>
  <Sheet.Content side="left" class="pr-0">
    <MobileLink href="/" class="flex items-center" bind:open>
      <Logo class="mr-4 h-8 w-8" />
      <span class="font-bold">{m["site.name"]()}</span>
    </MobileLink>
    <ScrollArea orientation="both" class="my-4 h-[calc(100vh-8rem)] pb-10 pl-1">
      <div class="flex flex-col space-y-3">
        {#each navigation as navItem}
          {#if navItem.href}
            <MobileLink href={navItem.href} bind:open class="text-foreground">
              {navItem.getTitle()}
            </MobileLink>
          {/if}
        {/each}
      </div>
      <div class="mt-6 border-t pt-4">
        <div class="flex items-center space-x-2">
          <LanguagePicker />
          <ModeToggle />
        </div>
      </div>
    </ScrollArea>
  </Sheet.Content>
</Sheet.Root>
