<script lang="ts">
  import { page } from "$app/state";
  import { ArrowUpRight, RotateCw, Search } from "@lucide/svelte";
  import { errorPresentation } from "$lib/error-presentation";
  let problem = $derived(errorPresentation(page.status));
</script>

<svelte:head
  ><title>{problem.status} · {problem.title} | uwcourses</title></svelte:head
>

<section class="error-page" aria-labelledby="error-title">
  <div class="error-art" aria-hidden="true">
    <span class="error-number">{problem.status}</span>
    <svg viewBox="0 0 600 340" fill="none">
      <path
        class="route-muted"
        d="M-20 260H105Q145 260 145 220V190Q145 150 185 150H245M365 150H415Q455 150 455 110V85Q455 45 495 45H620"
      />
      <path
        class="route-active"
        d="M-20 260H105Q145 260 145 220V190Q145 150 185 150H245"
      />
      <path class="gap" d="M265 150H345" />
      <circle cx="145" cy="240" r="8" /><circle cx="245" cy="150" r="10" />
      <circle class="destination" cx="365" cy="150" r="10" /><circle
        cx="455"
        cy="65"
        r="8"
      />
      <circle class="pulse" cx="245" cy="150" r="20" />
    </svg>
  </div>
  <div class="error-copy">
    <p class="error-label"><span></span>{problem.status} / {problem.label}</p>
    <h1 id="error-title">{problem.title}</h1>
    <p class="description">{problem.description}</p>
    {#if !problem.retry}
      <form action="/search" method="GET" class="error-search">
        <Search size={19} aria-hidden="true" />
        <input
          name="q"
          aria-label="Search courses"
          placeholder="Find a course or topic…"
        />
        <button aria-label="Search"><ArrowUpRight size={20} /></button>
      </form>
    {/if}
    <div class="error-actions">
      {#if problem.retry}<button
          class="retry"
          onclick={() => window.location.reload()}
          ><RotateCw size={16} />Try again</button
        >{/if}
      <a href="/search">Explore courses <ArrowUpRight size={16} /></a>
      <a href="/">Back home <ArrowUpRight size={16} /></a>
    </div>
  </div>
</section>

<style>
  .error-page {
    min-height: min(720px, 76svh);
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: center;
    gap: clamp(32px, 6vw, 96px);
    padding: 64px 0 96px;
  }
  .error-art {
    position: relative;
    aspect-ratio: 6 / 4;
    display: grid;
    place-items: center;
    overflow: hidden;
    mask-image: linear-gradient(
      90deg,
      transparent,
      #000 12%,
      #000 88%,
      transparent
    );
  }
  .error-number {
    font-size: clamp(160px, 22vw, 320px);
    font-weight: 550;
    letter-spacing: -0.08em;
    line-height: 1;
    color: var(--text);
    opacity: 0.08;
  }
  svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    stroke-width: 2;
  }
  .route-muted,
  .gap {
    stroke: var(--border);
  }
  .gap {
    stroke-dasharray: 3 9;
  }
  .route-active {
    stroke: var(--accent);
    stroke-dasharray: 450;
    animation: draw 1.4s var(--motion-ease) both;
  }
  circle {
    fill: var(--bg);
    stroke: var(--accent);
  }
  .destination {
    stroke: var(--muted);
  }
  .pulse {
    opacity: 0.3;
    animation: pulse 3s ease-out infinite;
    transform-box: fill-box;
    transform-origin: center;
  }
  .error-label {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--muted);
    font-size: 13px;
    margin: 0 0 24px;
  }
  .error-label span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }
  h1 {
    font-size: clamp(36px, 4.2vw, 64px);
    font-weight: 500;
    line-height: 1.05;
    letter-spacing: -0.045em;
    margin: 0;
    text-wrap: balance;
  }
  .description {
    font-size: 17px;
    line-height: 1.65;
    color: var(--muted);
    max-width: 36ch;
    margin: 24px 0 32px;
  }
  .error-search {
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid var(--muted);
    padding: 8px 0;
    max-width: 420px;
  }
  .error-search :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
  }
  input {
    min-width: 0;
    flex: 1;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    padding: 10px 0;
    outline: none;
  }
  .error-search:focus-within {
    border-color: var(--accent);
  }
  button {
    cursor: pointer;
    font: inherit;
  }
  .error-search button {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border: 0;
    background: transparent;
  }
  .error-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    align-items: center;
    margin-top: 28px;
    font-size: 14px;
  }
  .error-actions a,
  .retry {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .retry {
    padding: 12px 18px;
    border: 1px solid var(--border);
    border-radius: var(--radius-control);
    background: var(--surface);
    color: var(--text);
  }
  .error-actions a:hover,
  .retry:hover {
    color: var(--accent);
  }
  @keyframes draw {
    from {
      stroke-dashoffset: 450;
    }
    to {
      stroke-dashoffset: 0;
    }
  }
  @keyframes pulse {
    0% {
      transform: scale(0.7);
      opacity: 0.4;
    }
    100% {
      transform: scale(1.8);
      opacity: 0;
    }
  }
  @media (max-width: 760px) {
    .error-page {
      grid-template-columns: 1fr;
      gap: 0;
      padding: 16px 0 64px;
    }
    .error-art {
      max-height: 260px;
    }
    .error-number {
      font-size: 220px;
    }
    .error-copy {
      max-width: 480px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .route-active,
    .pulse {
      animation: none;
    }
  }
</style>
