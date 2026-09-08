<script lang="ts">
  import "../app.css";
  import { Sun, Moon, Monitor } from "@lucide/svelte";
  import { page } from "$app/state";
  import { onMount } from "svelte";
  let { data, children } = $props();
  let theme = $state("system");
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

<svelte:head
  ><meta
    name="description"
    content="Explore UW–Madison courses, professors, grades and prerequisites."
  /></svelte:head
>
<a class="skip-link" href="#main">Skip to content</a>
<header>
  <nav aria-label="Main navigation">
    <a class="brand" href="/"
      ><img src="/uw-coursemap-logo.svg" alt="" width="28" height="28" />uw<span
        >courses</span
      ></a
    >
    <div class="row">
      <a href="/search">explore</a><a href="/subjects">departments</a>
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
</header>
<main class="page" id="main">
  {#key page.url.pathname}{@render children()}{/key}
</main>
<footer class="page row between">
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
</footer>

<style>
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
    font: 12px var(--font-mono);
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
    }
    nav .row {
      gap: 12px;
      font-size: 11px;
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
