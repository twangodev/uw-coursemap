<script lang="ts">
	import '../app.css';
    import Navbar from "$lib/components/nav/navbar.svelte";
    import Footer from "$lib/components/footer/footer.svelte";
    import {ModeWatcher} from "mode-watcher";
    import {Toaster} from "$lib/components/ui/sonner";
	let { children } = $props();
</script>

<svelte:head>
    <title>UW Course Map</title>
    <meta name="description" content="Explore the courses offered by the UW-Madison in a visual and interactive way." />
    <meta name="keywords" content="UW-Madison, course map, course explorer, university courses" />
    <script defer src="https://analytics.twango.dev/script.js" data-website-id="e9ccd1f1-8138-4a41-a59b-dfedd30b4744"></script>
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