<script lang="ts">
  import { Languages, Check } from "@lucide/svelte";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import { Button } from "$lib/components/ui/button";
  import { getLocale, setLocale, type Locale } from "$lib/paraglide/runtime";
  import { languages } from "$lib/config/languages.js";

  function handleLanguageChange(locale: Locale) {
    setLocale(locale);
  }

  const currentLanguage = getLocale();
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger>
    <Button variant="ghost" class="h-8 w-8 px-0">
      <Languages class="h-[1.2rem] w-[1.2rem]" />
      <span class="sr-only">Change language</span>
    </Button>
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="end">
    {#each languages as lang}
      <DropdownMenu.Item
        onclick={() => handleLanguageChange(lang.locale)}
        class={`flex items-center ${lang.locale === currentLanguage ? "bg-accent" : ""}`}
      >
        <div class="mr-2 h-4 w-6 overflow-hidden rounded-sm">
          <svelte:component this={lang.flag} size="100%" />
        </div>
        {lang.nativeName}
        {#if lang.locale === currentLanguage}
          <Check class="ml-auto h-3 w-3" />
        {/if}
      </DropdownMenu.Item>
    {/each}
  </DropdownMenu.Content>
</DropdownMenu.Root>