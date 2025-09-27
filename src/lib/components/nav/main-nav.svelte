<script lang="ts">
  import Logo from "$lib/components/logo.svelte";
  import { navigation } from "$lib/config/navigation.ts";
  import { m } from "$lib/paraglide/messages";
  import { localizeHref } from "$lib/paraglide/runtime";

  import { page } from "$app/state";

  let currentPath = $derived(page.url.pathname.toLowerCase());
</script>

<div class="mr-4 hidden md:flex">
  <a
    href={localizeHref("/")}
    class="flex items-center gap-4 text-lg font-semibold whitespace-nowrap md:text-lg"
  >
    <Logo />
    <span class="hidden font-bold xl:inline-block">
      {m["site.name"]()}
    </span>
  </a>
  <nav class="mx-6 flex items-center gap-6 text-sm">
    {#each navigation as item}
      {@const localizedHref = item.href.startsWith('http') ? item.href : localizeHref(item.href)}
      <a
        href={localizedHref}
        class={`transition-colors ${currentPath === localizedHref?.toLowerCase() ? "text-foreground" : "text-muted-foreground hover:text-foreground"}`}
      >
        {item.getTitle()}
      </a>
    {/each}
  </nav>
</div>
