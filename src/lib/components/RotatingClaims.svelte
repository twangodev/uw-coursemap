<script lang="ts">
  import { onMount } from "svelte";
  import { ArrowUpRight, ChevronLeft, ChevronRight, Pause, Play } from "@lucide/svelte";
  import Claims from "./Claims.svelte";
  import type { Claim } from "$lib/types";

  let { claims, reviewFiles = [] }: { claims: Claim[]; reviewFiles?: string[] } = $props();
  let index = $state(0);
  let paused = $state(false);
  let container: HTMLDivElement;
  const items = $derived(claims.filter((claim, i) => claims.findIndex((other) => other.text === claim.text) === i));
  const current = $derived(items[index % Math.max(items.length, 1)]);
  function move(step: number) {
    index = (index + step + items.length) % items.length;
  }
  onMount(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    paused = motion.matches;
    const onMotion = () => { if (motion.matches) paused = true; };
    motion.addEventListener("change", onMotion);
    const timer = window.setInterval(() => {
      if (items.length < 2 || paused || document.hidden || container.matches(":hover") || container.contains(document.activeElement) || container.querySelector("[data-citation-trigger][aria-expanded=true]")) return;
      move(1);
    }, 8000);
    return () => {
      window.clearInterval(timer);
      motion.removeEventListener("change", onMotion);
    };
  });
</script>

<div bind:this={container} role="region" aria-label="Student takeaways" aria-roledescription="carousel">
  <div class="takeaway-heading">
    <h2><a href="#experience">What to expect <ArrowUpRight size={14} /></a></h2>
  {#if items.length > 1}
    <div class="controls">
      <button aria-label="Previous takeaway" onclick={() => { paused = true; move(-1); }}><ChevronLeft size={15} /></button>
      <span>{index % items.length + 1} / {items.length}</span>
      <button aria-label="Next takeaway" onclick={() => { paused = true; move(1); }}><ChevronRight size={15} /></button>
      <button aria-label={paused ? "Resume takeaway rotation" : "Pause takeaway rotation"} onclick={() => paused = !paused}>
        {#if paused}<Play size={13} />{:else}<Pause size={13} />{/if}
      </button>
    </div>
  {/if}
  </div>
  {#if current}
    {#key current.text}
      <div class="takeaway" role="group" aria-label={`${index % items.length + 1} of ${items.length}`}>
        <Claims claims={[current]} {reviewFiles} />
      </div>
    {/key}
  {/if}

</div>

<style>
  .takeaway-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
  h2 { margin: 0; font-size: 18px; font-weight: 500; }
  h2 a { display: inline-flex; align-items: center; gap: 8px; color: inherit; text-decoration: none; }
  h2 a :global(svg) { color: var(--muted); }
  .controls { flex-shrink: 0; }
  .controls span { min-width: 28px; text-align: center; }

  .controls { display: flex; align-items: center; gap: 2px; color: var(--muted); font-size: 12px; }
  button { display: grid; place-items: center; width: 30px; height: 30px; padding: 0; border: 0; background: transparent; color: inherit; cursor: pointer; border-radius: 4px; }
  button:hover { color: var(--text); background: var(--border); }
  button:focus-visible { outline: 2px solid var(--text); outline-offset: 2px; }
  @media (prefers-reduced-motion: no-preference) {
    .takeaway { animation: appear 350ms ease-out; }
    @keyframes appear { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
  }
</style>
