<script>
    import { Menu, Search } from "lucide-svelte";
    import * as Sheet from "$lib/components/ui/sheet";
    import { Button } from "$lib/components/ui/button/index.ts";
    import { Input } from "$lib/components/ui/input/index.ts";
    import Crest from "$lib/components/Crest.svelte";

    // SvelteKit-specific
    import { page } from "$app/stores";
    $: currentPath = $page.url.pathname;
</script>

<header class="bg-background top-0 flex min-h-16 items-center gap-4 border-b px-4 md:px-8">
    <nav class="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-base lg:gap-6">
        <a
                href="/"
                class="flex items-center gap-4 text-lg font-semibold md:text-lg whitespace-nowrap">
            <Crest/>
            <span>UW Course Map</span>
        </a>
        <a
                href="/"
                class={`transition-colors ${currentPath === '/' ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
            Home
        </a>
        <a
                href="/explorer"
                class={`transition-colors ${currentPath === '/explorer' ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
            Explorer
        </a>
    </nav>
    <Sheet.Root>
        <Sheet.Trigger asChild let:builder>
            <Button
                    variant="outline"
                    size="icon"
                    class="shrink-0 md:hidden"
                    builders={[builder]}
            >
                <Menu class="h-5 w-5" />
                <span class="sr-only">Toggle navigation menu</span>
            </Button>
        </Sheet.Trigger>
        <Sheet.Content side="left">
            <nav class="grid gap-6 text-lg font-medium">
                <a
                        href="/"
                        class={`flex items-center gap-4 text-lg font-semibold md:text-lg whitespace-nowrap ${currentPath === '/' ? 'text-foreground' : 'text-muted-foreground'}`}>
                    <Crest/>
                    <span>UW Course Map</span>
                </a>
                <a
                        href="/"
                        class={`hover:text-foreground ${currentPath === '/' ? 'text-foreground' : 'text-muted-foreground'}`}>
                    Home
                </a>
                <a
                        href="/explorer"
                        class={`hover:text-foreground ${currentPath === '/explorer' ? 'text-foreground' : 'text-muted-foreground'}`}>
                    Explorer
                </a>
            </nav>
        </Sheet.Content>
    </Sheet.Root>
    <div class="flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
        <form class="ml-auto flex-1 sm:flex-initial">
            <div class="relative">
                <Search class="text-muted-foreground absolute left-2.5 top-2.5 h-4 w-4" />
                <Input
                        type="search"
                        placeholder="Search courses, programs..."
                        class="pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
                />
            </div>
        </form>
    </div>
</header>
