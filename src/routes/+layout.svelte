<script lang="ts">
	import '../app.css';
    import Navbar from "$lib/components/nav/Navbar.svelte";
    import Footer from "$lib/components/footer/Footer.svelte";
	let { children } = $props();
</script>

<div class="flex flex-col min-h-screen h-screen">
    <Navbar/>
    <main class="flex-grow flex">
        {@render children()}
    </main>
    <Footer/>
</div>