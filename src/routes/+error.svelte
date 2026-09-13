<script lang="ts">
  import { page } from "$app/state";
  import { ArrowUpRight, RotateCw, Search } from "@lucide/svelte";
  import { errorPresentation } from "$lib/error-presentation";
  let problem = $derived(errorPresentation(page.status));
</script>

<svelte:head
  ><title>{problem.status} · {problem.title} | uwcourses</title></svelte:head
>

<section
  class="min-h-[min(720px,_76svh)] grid grid-cols-[1fr_1fr] items-center gap-[clamp(32px,_6vw,_96px)] pt-16 pb-24 error-page px-0"
  aria-labelledby="error-title"
>
  <div
    class="relative [aspect-ratio:6_/_4] grid place-items-center overflow-hidden error-art"
    aria-hidden="true"
  >
    <span
      class="text-[clamp(160px,_22vw,_320px)] font-[550] tracking-[-0.08em] leading-[1] text-foreground opacity-[0.08] error-number"
      >{problem.status}</span
    >
  </div>
  <div class="error-copy">
    <p
      class="flex items-center gap-2.5 text-muted text-[13px] mt-0 mb-6 error-label mx-0"
    >
      <span class="w-1.5 h-1.5 rounded-[50%] bg-accent"></span>{problem.status} /
      {problem.label}
    </p>
    <h1
      class="text-[clamp(36px,_4.2vw,_64px)] font-medium leading-[1.05] tracking-[-0.045em] m-0 text-balance"
      id="error-title"
    >
      {problem.title}
    </h1>
    <p
      class="text-[17px] leading-[1.65] text-muted max-w-[36ch] mt-6 mb-8 description mx-0"
    >
      {problem.description}
    </p>
    {#if !problem.retry}
      <form
        action="/search"
        method="GET"
        class="flex items-center gap-3 border-b border-b-muted max-w-105 error-search py-2 px-0"
      >
        <Search size={19} aria-hidden="true" />
        <input
          class="min-w-0 border-0 bg-transparent text-foreground [outline:none] py-2.5 px-0"
          name="q"
          aria-label="Search courses"
          placeholder="Find a course or topic…"
        />
        <button
          class="cursor-pointer grid place-items-center w-11 h-11 border-0 bg-transparent"
          aria-label="Search"><ArrowUpRight size={20} /></button
        >
      </form>
    {/if}
    <div
      class="flex flex-wrap gap-6 items-center mt-7 text-[14px] error-actions"
    >
      {#if problem.retry}<button
          class="cursor-pointer inline-flex items-center gap-2 border border-border rounded-[var(--radius-control)] bg-surface text-foreground retry py-3 px-4.5"
          onclick={() => window.location.reload()}
          ><RotateCw size={16} />Try again</button
        >{/if}
      <a class="inline-flex items-center gap-2" href="/search"
        >Explore courses <ArrowUpRight size={16} /></a
      >
      <a class="inline-flex items-center gap-2" href="/"
        >Back home <ArrowUpRight size={16} /></a
      >
    </div>
  </div>
</section>

<style>
  .error-art {
    mask-image: linear-gradient(
      90deg,
      transparent,
      #000 12%,
      #000 88%,
      transparent
    );
  }
  .error-search :global(svg) {
    color: var(--muted);
    flex-shrink: 0;
  }
  input {
    flex: 1;
    font: inherit;
  }
  .error-search:focus-within {
    border-color: var(--accent);
  }
  button {
    font: inherit;
  }
  .error-actions a:hover,
  .retry:hover {
    color: var(--accent);
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
</style>
