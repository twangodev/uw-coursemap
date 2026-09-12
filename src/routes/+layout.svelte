<script lang="ts">
  import "../app.css";
  import { representationUrl, isDocument } from "$lib/documents";
  import { pageSeo, jsonLd } from "$lib/seo";
  import { Sun, Moon, Monitor } from "@lucide/svelte";
  import { page } from "$app/state";
  import { dev } from "$app/environment";
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
  {#if !dev && page.url.origin === "https://uwcourses.com"}
    <script src="https://rybbit.twango.dev/api/script.js" data-site-id="1" defer></script>
  {/if}
  <link rel="service-desc" type="application/vnd.oai.openapi+json" href="https://uwcourses.com/openapi.json" />
  <link rel="api-catalog" type="application/linkset+json" href="https://uwcourses.com/.well-known/api-catalog" />
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
      {#each [{ href: "/search", label: "courses", active: /^\/(search|courses)(\/|$)/.test(page.url.pathname) }, { href: "/departments", label: "departments", active: page.url.pathname.startsWith("/departments") }, { href: "/instructors/by-rating-count", label: "instructors", active: page.url.pathname.startsWith("/instructors") }] as link}
        <a href={link.href} aria-current={link.active ? "page" : undefined}>{link.label}</a>
      {/each}
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
{#if !fullscreenMap}<footer class="page">
  <div>
    <p class="site-credit">Made by <a href="https://twango.dev/?utm_source=uwcourses.com">James Ding</a> and <a href="https://github.com/twangodev/uwcourses/graphs/contributors">contributors</a>.</p>
    <p class="muted">
      Not affiliated with or endorsed by the University of Wisconsin–Madison.
    </p>
  </div>
  <div class="footer-resources">
    <nav class="footer-links" aria-label="Resources">
      <a href="/stats">Stats</a>
      <a href="/openapi">API</a>
      <a href="https://github.com/twangodev/uwcourses">GitHub</a>
      <a href={`https://huggingface.co/datasets/${data.status.repository}/tree/${data.status.revision}`}>Dataset</a>
    </nav>
    <p class="muted scan-date">Scanned {data.status.observed_at.slice(0, 10)}</p>
  </div>
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
  header nav {
    max-width: 1380px;
    margin: auto;
    padding: 1rem 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  header nav a[aria-current="page"] { color: var(--accent); }
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
  header nav .row {
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
  header nav .row {
    flex-wrap: nowrap;
  }

  .site-credit { margin: 0 0 6px; }

  .footer-resources { flex-shrink: 0; text-align: right; }
  .footer-links { display: flex; justify-content: flex-end; gap: 1.25rem; }
  .footer-links a { padding: 0.25rem 0; }
  .scan-date { margin: 6px 0 0; }

  footer.page {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.5rem 3rem;
    border-top: 1px solid var(--border);
    font-size: 0.8rem;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
  }
  @media (max-width: 640px) {
    footer.page { flex-direction: column; }
    .footer-resources { text-align: left; }
    .footer-links { justify-content: flex-start; }
    header nav {
      padding: 1rem;
      flex-wrap: wrap;
    }
    header nav .row {
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
