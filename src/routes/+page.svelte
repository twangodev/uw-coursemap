<script lang="ts">
  import { ArrowUpRight, Search } from "@lucide/svelte";
  import SearchInput from "$lib/components/SearchInput.svelte";
  import CampusScene from "$lib/components/CampusScene.svelte";
  import campusMap from "$lib/assets/campus-map.svg";
  let { data } = $props();
  let departments = $derived(
    [...data.status.departments].sort((a, b) => b.count - a.count).slice(0, 8),
  );
</script>

<section class="landing" aria-labelledby="landing-title">
  <h1 id="landing-title" class="sr-only">UW–Madison courses</h1>
  <img class="campus-map" src={campusMap} alt="" width="900" height="505" />
  <CampusScene coverage={data.campus} />
  <div class="landing-copy">
    <form action="/search" class="landing-search">
      <SearchInput
        revision={data.status.revision}
        label="Search courses or topics"
        placeholder="A course, professor, or topic…"
      />
      <button aria-label="Find courses"
        ><Search size={19} strokeWidth={1.5} /></button
      >
    </form>
    <div class="try-search">
      <span>Try</span><a href="/courses/COMPSCI_300">CS 300</a><a
        href="/search?q=climate">climate</a
      ><a href="/search?q=film">film</a>
    </div>
  </div>
  <a class="map-credit" href="https://www.openstreetmap.org/copyright"
    >© OpenStreetMap contributors</a
  >
</section>
<div class="campus-strip">
  <span
    >{data.status.courses.toLocaleString()} courses. Plenty of possibilities.</span
  ><a href="/search">Explore all courses <ArrowUpRight size={15} /></a>
</div>
<section class="discover" aria-labelledby="discover-title">
  <div class="discover-intro">
    <h2 id="discover-title">Follow your curiosity.</h2>
    <p class="muted">
      Start in your department.<br />Or somewhere entirely new.
    </p>
    <a href="/departments">All departments <ArrowUpRight size={14} /></a>
  </div>
  <div class="department-list">
    {#each departments as d}<a
        href={"/departments/" + encodeURIComponent(d.subject)}
        ><span>{d.subject}</span><span class="department-count"
          >{d.count} courses <ArrowUpRight size={14} /></span
        ></a
      >{/each}
  </div>
</section>

<style>
  .landing {
    position: relative;
    isolation: isolate;
    padding: 30px 0 40px;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .campus-map {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center 48%;
    z-index: -1;
    opacity: 0.35;
    pointer-events: none;
    mask-image: linear-gradient(transparent, #000 20%, #000 70%, transparent);
  }
  :global(.dark) .campus-map {
    filter: invert(1);
    opacity: 0.24;
  }
  .landing-copy {
    position: relative;
    width: min(100%, 640px);
    margin: 0 auto;
  }
  .map-credit {
    display: block;
    width: fit-content;
    margin: 24px 0 0 auto;
    font-size: 9px;
    color: var(--muted);
    text-decoration: none;
  }
  .landing-search {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 7px 7px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-top: 12px;
    background: var(--bg);
    width: 100%;
  }
  .landing-search:focus-within {
    border-color: var(--accent);
  }
  button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-shrink: 0;
    min-height: 42px;
    padding: 8px 10px;
    font-size: 14px;
    background: transparent;
    color: var(--text);
    border: 0;
  }
  button:hover {
    opacity: 0.85;
  }
  .try-search {
    display: flex;
    justify-content: center;
    gap: 18px;
    margin-top: 14px;
    font-size: 13px;
  }
  .try-search span {
    color: var(--muted);
  }
  .try-search a {
    text-decoration: underline;
    text-decoration-color: var(--border);
    text-underline-offset: 4px;
  }
  .campus-strip {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 21px 0;
    border-block: 1px solid var(--border);
    font-size: 14px;
  }
  .campus-strip a,
  .discover-intro a {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .discover {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 64px;
    padding: 42px 0 10px;
  }
  .discover h2 {
    font-size: 25px;
  }
  .discover-intro p {
    margin-top: 12px;
    line-height: 1.6;
  }
  .discover-intro a {
    margin-top: 24px;
    font-size: 13px;
  }
  .department-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 36px;
  }
  .department-list a {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 17px 0;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
  }
  .department-count {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    color: var(--muted);
    font: 11px var(--font-sans);
    white-space: nowrap;
  }
  @media (max-width: 760px) {
    .landing {
      padding: 20px 0 24px;
    }
    .campus-map {
      object-position: 58% center;
      opacity: 0.35;
    }
    .campus-strip {
      font-size: 13px;
      flex-wrap: wrap;
    }
    .discover {
      grid-template-columns: 1fr;
      gap: 24px;
      padding-top: 28px;
    }
    .department-list {
      column-gap: 20px;
    }
    .department-list a {
      align-items: start;
      flex-direction: column;
      gap: 5px;
    }
  }
  @media (prefers-reduced-motion: no-preference) {
    .landing-copy {
      animation: landing-arrive var(--motion-travel) var(--motion-ease) both;
    }
    .landing-search button :global(svg) {
      transition: transform 180ms ease;
    }
    .landing-search button:hover :global(svg) {
      transform: translate(2px, -2px);
    }
    @keyframes landing-arrive {
      from {
        opacity: 0;
        transform: translateY(6px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  }
</style>
