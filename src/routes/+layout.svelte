<script lang="ts">
  import "../app.css";
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
      >uw<span>courses</span><span class="dot">.</span></a
    >
    <div class="row">
      <a href="/search">explore</a><a href="/subjects">departments</a><label
        class="sr-only"
        for="theme">Color theme</label
      ><select id="theme" bind:value={theme} onchange={apply}
        ><option value="system">System</option><option value="light"
          >Light</option
        ><option value="dark">Dark</option></select
      >
    </div>
  </nav>
</header>
<main class="page" id="main">
  {#key page.url.pathname}{@render children()}{/key}
</main>
<footer class="page row between">
  <div>
    <p>Made for curious Badgers.</p>
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
    font-size: 1.6rem;
    font-weight: 650;
    letter-spacing: -0.05em;
    color: var(--text);
  }
  .brand span {
    font-weight: 400;
  }
  .brand .dot {
    color: var(--accent);
  }
  nav .row {
    font: 11px var(--font-mono);
  }
  select {
    font-size: 0.75rem;
    padding: 0.25rem;
  }
  footer.page {
    border-top: 1px solid var(--border);
    font-size: 0.8rem;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
  }
  @media (max-width: 640px) {
    nav {
      padding: 1rem 1.2rem;
    }
    nav .row {
      gap: 0.7rem;
    }
  }
</style>
