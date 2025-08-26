<script lang="ts">
  import "../app.css";
  import Navbar from "$lib/components/nav/navbar.svelte";
  import Footer from "$lib/components/footer/footer.svelte";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "$lib/components/ui/sonner";
  import { page } from "$app/state";
  import NavigationOverlay from "$lib/components/navigation-overlay.svelte";
  import type { WebSite, WithContext } from "schema-dts";
  
  let { children, data } = $props();

  const siteName = "UW Course Map";
  const siteDescription =
    "Explore the courses offered by the UW-Madison in a visual and interactive way.";

  let title = $derived.by(() => {
    const subtitle = page.data?.subtitle;
    if (!subtitle) {
      return siteName;
    }
    return `${subtitle} | ${siteName}`;
  });

  let description = $derived(page.data?.description || siteDescription);
  let ogImage = $derived(page.data?.ogImage || "https://uwcourses.com/uw-coursemap-logo.svg");
  let canonicalUrl = $derived(`https://uwcourses.com${page.url.pathname}`);

  const website: WithContext<WebSite> = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: siteName,
    url: "https://uwcourses.com",
    description: siteDescription,
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: "https://uwcourses.com/explorer?search={search_term_string}"
      },
      query: "required name=search_term_string"
    }
  };

  let jsonLd = $derived([website, ...(page.data?.jsonLd || [])]);
</script>

<svelte:head>
  <title>{title}</title>
  <link rel="icon" href="/favicon.ico" />
  <link rel="canonical" href={canonicalUrl} />
  
  <!-- Primary Meta Tags -->
  <meta name="title" content={title} />
  <meta name="description" content={description} />
  <meta name="author" content="UW Course Map" />
  <meta name="theme-color" content="#c5050c" />
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content={canonicalUrl} />
  <meta property="og:site_name" content={siteName} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:image" content={ogImage} />
  <meta property="og:locale" content="en_US" />
  
  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image" />
  <meta property="twitter:url" content={canonicalUrl} />
  <meta property="twitter:title" content={title} />
  <meta property="twitter:description" content={description} />
  <meta property="twitter:image" content={ogImage} />
  
  <!-- Additional SEO -->
  <meta name="robots" content="index, follow" />
  <meta name="googlebot" content="index, follow, max-video-preview:-1, max-image-preview:large, max-snippet:-1" />
  
  <!-- Analytics -->
  <script
    src="https://rybbit.twango.dev/api/script.js"
    data-site-id="1"
    data-track-errors="true"
    data-web-vitals="true"
    defer
  ></script>
  
  <!-- Structured Data -->
  {@html `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>`}
</svelte:head>

<Toaster />
<ModeWatcher />
<NavigationOverlay />
<div class="flex h-screen min-h-screen flex-col">
  <Navbar />
  <main class="flex grow">
    {@render children?.()}
  </main>
  <Footer lastSynced={data.lastSynced} />
</div>
