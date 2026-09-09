<script lang="ts">
  import "../app.css";
  import { pageSeo, jsonLd } from "$lib/seo";
  import { Sun, Moon, Monitor } from "@lucide/svelte";
  import { page } from "$app/state";
  import { onMount } from "svelte";
  let { data, children } = $props();
  let seo = $derived(pageSeo(page.data, page.url.pathname, page.status));
  let theme = $state("system");
  let fullscreenMap = $derived(/^\/explorer\/[^/]+\/?$/.test(page.url.pathname));
  function apply() {
    document.documentElement.classList.toggle(
      "dark",
      theme === "dark" ||
        (theme === "system" &&
          matchMedia("(prefers-color-scheme: dark)").matches),
    );
    try {
      if (theme === "system") localStorage.removeItem("theme");
      else localStorage.setItem("theme", theme);
    } catch {}
  }
  onMount(() => {
    document.documentElement.dataset.hydrated = "true";
    try {
      theme = localStorage.getItem("theme") || "system";
    } catch {}
    const media = matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  });
</script>

<svelte:head>
  <title>{seo.title}</title>
  <meta name="description" content={seo.description} />
  <link rel="canonical" href={seo.canonical} />
  <meta name="robots" content={seo.noindex ? "noindex,follow" : "index,follow,max-image-preview:large"} />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="UW Courses" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:title" content={seo.title} />
  <meta property="og:description" content={seo.description} />
  <meta property="og:url" content={seo.canonical} />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content={seo.title} />
  <meta name="twitter:description" content={seo.description} />
  {@html `<script type="application/ld+json">${jsonLd(seo.structuredData)}</script>`}
</svelte:head>

<a class="skip-link" href="#main">Skip to content</a>
{#if !fullscreenMap}<header>
  <nav aria-label="Main navigation">
    <a class="brand" href="/"
      ><img src="/uw-coursemap-logo.svg" alt="" width="28" height="28" />uw<span
        >courses</span
      ></a
    >
    <div class="row">
      <a href="/search">courses</a><a href="/departments">departments</a><a href="/instructors/by-rating-count">instructors</a>
      <div class="theme-control">
        {#if theme === "dark"}<Moon size={16} />{:else if theme === "light"}<Sun
            size={16}
          />{:else}<Monitor size={16} />{/if}
        <label class="sr-only" for="theme">Color theme</label>
        <select id="theme" bind:value={theme} onchange={apply}
          ><option value="system">System</option><option value="light"
            >Light</option
          ><option value="dark">Dark</option></select
        >
      </div>
    </div>
  </nav>
</header>{/if}
<main class="page" class:map-page={fullscreenMap} id="main">
  {#key page.url.pathname}<div class="route-content">
      {@render children()}
    </div>{/key}
</main>
{#if !fullscreenMap}<footer class="page row between">
  <div>
    <p class="muted">
      Not affiliated with or endorsed by the University of Wisconsin–Madison.
    </p>
  </div>
  <a
    class="mono"
    href={`https://huggingface.co/datasets/${data.status.repository}/tree/${data.status.revision}`}
    >Dataset · scanned {data.status.observed_at.slice(0, 10)}</a
  >
</footer>{/if}

<style>
  .page.map-page { max-width: none; padding: 0; margin: 0; }
  .map-page .route-content { animation: none; transform: none; }
  .skip-link {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 100;
    padding: 0.5rem 1rem;
    background: var(--bg);
    border: 1px solid var(--accent);
    clip-path: inset(50%);
  }
  .skip-link:focus {
    clip-path: none;
  }
  header {
    border-bottom: 1px solid var(--border);
  }
  nav {
    max-width: 1380px;
    margin: auto;
    padding: 1rem 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    font-size: 1.6rem;
    font-weight: 650;
    letter-spacing: -0.05em;
    color: var(--text);
  }
  .brand span {
    font-weight: 400;
  }
  .brand img {
    margin-right: 9px;
  }
  nav .row {
    font: 14px var(--font-sans);
  }
  .theme-control {
    position: relative;
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    color: var(--muted);
  }
  .theme-control:focus-within {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: 4px;
  }
  select {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    padding: 0;
  }
  nav .row {
    flex-wrap: nowrap;
  }

  footer.page {
    border-top: 1px solid var(--border);
    font-size: 0.8rem;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
  }
  @media (max-width: 640px) {
    nav {
      padding: 1rem;
      flex-wrap: wrap;
    }
    nav .row {
      width: 100%;
      justify-content: space-between;
      gap: 12px;
      font-size: 13px;
    }
    .brand {
      font-size: 22px;
    }
    .brand img {
      width: 24px;
      height: 24px;
      margin-right: 6px;
    }
  }
</style>
