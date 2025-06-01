<script lang="ts">
    import { cn } from "$lib/utils.js";
    import Banner from "$lib/components/banner.svelte";
    import MainNav from "$lib/components/nav/main-nav.svelte";
    import {siteConfig} from "$lib/config/site.ts";
    import {buttonVariants} from "$lib/components/ui/button";
    import Search from "$lib/components/search.svelte";
    import MobileNav from "$lib/components/nav/mobile-nav.svelte";
    import ModeToggle from "$lib/components/mode-toggle.svelte";
    import Github from "$lib/components/icons/github.svelte";
</script>

<header
        class="border-border/40 bg-background/95 supports-backdrop-filter:bg-background/60 sticky top-0 z-50 w-full border-b backdrop-blur-sm"
>
    <Banner></Banner>
    <div class="container flex h-14 max-w-(--breakpoint-2xl) items-center">
        <MainNav />
        <MobileNav />
        <div class="flex flex-1 items-center justify-between space-x-2 md:justify-end">
            <div class="w-full flex-1 md:w-auto md:flex-none">
                <Search />
            </div>
            <nav class="flex items-center">
                <a href={siteConfig.links.github} target="_blank" rel="noopener noreferrer">
                    <div
                            class={cn(
							buttonVariants({
								size: "sm",
								variant: "ghost"
							}),
							"h-8 w-8 px-0"
						)}
                    >
                        <Github class="h-5 w-5" />
                        <span class="sr-only">GitHub</span>
                    </div>
                </a>
                <ModeToggle />
            </nav>
        </div>
    </div>
</header>
