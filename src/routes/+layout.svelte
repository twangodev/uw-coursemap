<script lang="ts">
	import '../app.css';
    import Navbar from "$lib/components/Navbar.svelte";
    import Footer from "$lib/components/Footer.svelte";
	let { children } = $props();
</script>

<div class="flex flex-col h-screen">
    <Navbar/>
    <main class="flex-grow">
        {@render children()}
    </main>
    <Footer/>
</div>