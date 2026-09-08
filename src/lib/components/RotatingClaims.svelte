<script lang="ts">
  import { onMount } from "svelte";
  import { Info, ChevronLeft, ChevronRight, Pause, Play } from "@lucide/svelte";
  import { Tooltip } from "bits-ui";
  import Claims from "./Claims.svelte";
  import type { Claim } from "$lib/types";

  let { claims, reviewFiles = [] }: { claims: Claim[]; reviewFiles?: string[] } = $props();
  let index = $state(0);
  let paused = $state(false);
  let infoOpen = $state(false);
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
    <div class="summary-title">
      <h2>Summary</h2>
      <Tooltip.Provider delayDuration={200}><Tooltip.Root bind:open={infoOpen} disableCloseOnTriggerClick>
        <Tooltip.Trigger class="summary-info" aria-label="About this summary" onclick={() => infoOpen = true}><Info size={14} /></Tooltip.Trigger>
        <Tooltip.Portal><Tooltip.Content role="tooltip" class="summary-info-content" sideOffset={6}>AI-generated from student reviews across all captured dates. Open the citations to read the original comments.</Tooltip.Content></Tooltip.Portal>
      </Tooltip.Root></Tooltip.Provider>
    </div>
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
  .takeaway-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
  h2 { margin: 0; font-size: 14px; font-weight: 550; color: var(--muted); }
  .summary-title { display: flex; align-items: center; gap: 6px; }
  :global(.summary-info) { display: grid; place-items: center; border: 0; padding: 3px; background: none; color: var(--muted); cursor: help; }
  :global(.summary-info-content) { z-index: 100; max-width: 250px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); color: var(--muted); font-size: 12px; line-height: 1.6; box-shadow: 0 5px 20px #0001; }
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
