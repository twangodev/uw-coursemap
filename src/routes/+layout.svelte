<script lang="ts">
  import "../app.css";
  import { representationUrl, isDocument } from "$lib/documents";
  import { pageSeo, jsonLd } from "$lib/seo";
  import { Sun, Moon, Monitor } from "@lucide/svelte";
  import { page } from "$app/state";
  import { onMount } from "svelte";
  let { data, children } = $props();
  let seo = $derived(pageSeo(page.data, page.url.pathname, page.status));
  const themes = ["system", "light", "dark"] as const;
  let theme = $state<(typeof themes)[number]>("system");
  let nextTheme = $derived(themes[(themes.indexOf(theme) + 1) % themes.length]);
  let themeLabel = $derived(`Color theme: ${theme}. Switch to ${nextTheme}`);
  function cycleTheme() {
    theme = nextTheme;
    apply();
  }
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
      const saved = localStorage.getItem("theme");
      theme = saved === "light" || saved === "dark" ? saved : "system";
    } catch {}
    const media = matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  });
</script>

<svelte:head>
  <link rel="service-desc" type="application/vnd.oai.openapi+json" href="https://uwcourses.com/openapi.json" />
  <title>{seo.title}</title>
  <meta name="description" content={seo.description} />
  <link rel="canonical" href={seo.canonical} />
  {#if page.status === 200 && isDocument(page.url.pathname)}
    <link rel="alternate" type="text/markdown" href={'https://uwcourses.com' + representationUrl(page.url.pathname, 'md', page.url.search)} />
    <link rel="alternate" type="application/json" href={'https://uwcourses.com' + representationUrl(page.url.pathname, 'json', page.url.search)} />
  {/if}
  <meta name="robots" content={seo.noindex ? "noindex,follow" : "index,follow,max-image-preview:large"} />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="UW Courses" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:title" content={seo.title} />
  <meta property="og:description" content={seo.description} />
  <meta property="og:url" content={seo.canonical} />
  <meta property="og:image" content={seo.image} />
  <meta property="og:image:type" content="image/png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content={seo.imageAlt} />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content={seo.image} />
  <meta name="twitter:image:alt" content={seo.imageAlt} />
  <meta name="twitter:title" content={seo.title} />
  <meta name="twitter:description" content={seo.description} />
  {@html `<script type="application/ld+json">${jsonLd(seo.structuredData)}</script>`}
</svelte:head>

<a class="skip-link" href="#main">Skip to content</a>
{#if !fullscreenMap}<header>
  <nav aria-label="Main navigation">
    <a class="brand" href="/"
      ><img src="/uwcourses-logo.svg" alt="" width="28" height="28" /><span
        >uwcourses</span
      ></a
    >
    <div class="row">
      <a href="/search">courses</a><a href="/departments">departments</a><a href="/instructors/by-rating-count">instructors</a>
      <button class="theme-control" type="button" aria-label={themeLabel} title={themeLabel} onclick={cycleTheme}>
        {#if theme === "dark"}<Moon size={16} />{:else if theme === "light"}<Sun size={16} />{:else}<Monitor size={16} />{/if}
      </button>
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
    <p class="site-credit">Made by <a href="https://twango.dev/?utm_source=uwcourses.com">James Ding</a> and <a href="https://github.com/twangodev/uwcourses/graphs/contributors">contributors</a>.</p>
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
  .brand img {
    margin-right: 9px;
  }
  nav .row {
    font: 14px var(--font-sans);
  }
  .theme-control {
    border: 0;
    padding: 0;
    background: transparent;
    cursor: pointer;
    border-radius: 4px;
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    color: var(--muted);
  }
  .theme-control:hover { color: var(--text); }
  .theme-control:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: 4px;
  }
  nav .row {
    flex-wrap: nowrap;
  }

  .site-credit { margin: 0 0 6px; }

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
