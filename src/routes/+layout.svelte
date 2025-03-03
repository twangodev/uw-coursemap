<script lang="ts">
	import '../app.css';
    import Navbar from "$lib/components/nav/Navbar.svelte";
    import Footer from "$lib/components/footer/Footer.svelte";
    import {ModeWatcher} from "mode-watcher";
	let { children } = $props();
</script>

<ModeWatcher/>
<div class="flex flex-col min-h-screen h-screen">
    <Navbar/>
    <main class="grow flex">
        {@render children?.()}
    </main>
    <Footer/>
</div>