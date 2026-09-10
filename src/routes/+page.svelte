<script lang="ts">
  import { ArrowUpRight, Search } from "@lucide/svelte";
  import SearchInput from "$lib/components/SearchInput.svelte";
  import CampusScene from "$lib/components/CampusScene.svelte";
  import { termName } from "$lib/format";
  let { data } = $props();
  let departments = $derived(
    [...data.status.departments].sort((a, b) => b.count - a.count).slice(0, 8),
  );
</script>

<section class="landing">
  <div class="landing-copy">
    <p class="semester">
      <span></span>{termName(data.status.term)} · UW–Madison
    </p>
    <h1>See you<br />on the Hill<span class="period">.</span></h1>
    <p class="landing-description">
      Find UW–Madison courses for your next semester. Compare grades, get to
      know your professors, and hear from the students who came before you.
    </p>
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
  <div class="landing-art"><CampusScene coverage={data.campus} /></div>
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
    display: grid;
    grid-template-columns: 1.05fr 1fr;
    align-items: center;
    gap: 20px;
    padding: 58px 0 60px;
    min-height: 575px;
  }
  .semester {
    font: 12px var(--font-sans);
    color: var(--muted);
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 28px;
  }
  .semester span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }
  h1 {
    font-size: clamp(54px, 6.8vw, 88px);
    line-height: 0.98;
    font-weight: 550;
    letter-spacing: -0.045em;
  }
  .period {
    color: var(--accent);
  }
  .landing-description {
    font-size: 18px;
    line-height: 1.55;
    max-width: 445px;
    margin-top: 26px;
    color: var(--muted);
  }
  .landing-search {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 7px 7px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-top: 30px;
    background: var(--bg);
    max-width: 530px;
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
  .landing-art {
    padding-top: 28px;
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
      grid-template-columns: 1fr;
      padding: 22px 0 28px;
      gap: 8px;
    }
    h1 {
      font-size: 64px;
    }
    .landing-description {
      font-size: 16px;
    }
    .landing-art {
      width: min(100%, 410px);
      margin: 0 auto;
      padding: 0;
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
    .landing-art {
      animation: landing-arrive 420ms 40ms var(--motion-ease) both;
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
