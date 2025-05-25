<script lang="ts">
	import '../app.css';
    import Navbar from "$lib/components/nav/navbar.svelte";
    import Footer from "$lib/components/footer/footer.svelte";
    import {ModeWatcher} from "mode-watcher";
    import {Toaster} from "$lib/components/ui/sonner";
    import { page } from '$app/state'
    import type {WebSite, WithContext} from "schema-dts";
	let { children } = $props();

    const siteName = "UW Course Map"
    const siteDescription = "Explore the courses offered by the UW-Madison in a visual and interactive way."

    let title = $derived.by(() => {
        const subtitle = page.data?.subtitle
        if (!subtitle) {
            return siteName
        }
        return `${subtitle} | ${siteName}`
    })

    let description = $derived(page.data?.description || siteDescription);

    const website: WithContext<WebSite> = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: siteName,
        url: 'https://uwcourses.com',
        description: siteDescription,
    }

    let jsonLd = $derived([
        website,
        ...(page.data?.jsonLd || []),
    ])

</script>

<svelte:head>
    <title>{title}</title>
    <link rel="icon" href="/favicon.ico">
    <meta name="description" content={description} />
    <meta name="keywords" content="UW-Madison, University of Wisconsin-Madison, course map, course explorer, university courses" />
    <script defer src="https://analytics.twango.dev/script.js" data-website-id="e9ccd1f1-8138-4a41-a59b-dfedd30b4744"></script>
    {@html `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>`}
</svelte:head>

<Toaster/>
<ModeWatcher/>
<div class="flex flex-col min-h-screen h-screen">
    <Navbar/>
    <main class="grow flex">
        {@render children?.()}
    </main>
    <Footer/>
</div>