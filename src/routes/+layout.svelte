<script lang="ts">
  import "../app.css";
  import Navbar from "$lib/components/nav/navbar.svelte";
  import Footer from "$lib/components/footer/footer.svelte";
  import SEOMeta from "$lib/components/seo/seo-meta.svelte";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "$lib/components/ui/sonner";
  import { page } from "$app/state";
  import NavigationOverlay from "$lib/components/navigation-overlay.svelte";

  let { children, data } = $props();
</script>

<!-- SEO Meta Tags -->
<SEOMeta
  subtitle={page.data?.subtitle}
  description={page.data?.description}
  ogImage={page.data?.ogImage}
  jsonLd={page.data?.jsonLd || []}
/>

<svelte:head>
  <link rel="icon" href="/favicon.ico" />
</svelte:head>

<ModeWatcher />
<Toaster />
<NavigationOverlay />
<div class="flex h-screen min-h-screen flex-col">
    <Navbar />
    <main class="flex grow">
        {@render children?.()}
    </main>
    <Footer lastSynced={data.lastSynced} />
</div>

