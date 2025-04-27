<script lang="ts">
    import Logo from "$lib/components/logo.svelte";
    import {siteConfig} from "$lib/config/site.ts";
    import {navigation} from "$lib/config/navigation.ts";

    import { page } from "$app/state";

    let currentPath = $derived(page.url.pathname.toLowerCase());

</script>

<div class="mr-4 hidden md:flex">
    <a
            href="/"
            class="flex items-center gap-4 text-lg font-semibold md:text-lg whitespace-nowrap">
        <Logo/>
        <span class="hidden font-bold xl:inline-block">
			{siteConfig.name}
		</span>
    </a>
    <nav class="flex items-center gap-6 text-sm mx-4">
        {#each navigation as item}
            <a
                    href={item.href}
                    class={`transition-colors ${currentPath === item.href?.toLowerCase() ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
                {item.title}
            </a>
        {/each}
    </nav>
</div>
