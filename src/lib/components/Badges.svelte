<script lang="ts">
  import { Popover } from 'bits-ui';
  import { onDestroy } from 'svelte';
  import { X } from '@lucide/svelte';
  import { safeUrl } from '$lib/format';
  import type { Badge } from '$lib/badges';
  let { badges, limit = 2 }: { badges: Badge[]; limit?: number } = $props();
  let group = $state<HTMLDivElement | null>(null);
  let active = $state<string | null>(null);
  let trigger = $state<HTMLButtonElement | null>(null);
  let content = $state<HTMLDivElement | null>(null);
  let selected = $derived(badges.slice(0, limit).find(b => b.id === active));
  let restoringFocus = false;
  let timer: ReturnType<typeof setTimeout>;
  function show(badge: Badge, element: HTMLButtonElement) { clearTimeout(timer); trigger = element; active = badge.id; }
  function leave() { clearTimeout(timer); timer = setTimeout(() => { if (!content?.contains(document.activeElement) && !trigger?.matches(':focus-visible')) active = null; }, 200); }
  function focusLeft(event: FocusEvent) {
    const next = event.relatedTarget as Node | null;
    if (next !== trigger && !content?.contains(next)) { clearTimeout(timer); active = null; }
  }
  onDestroy(() => clearTimeout(timer));
</script>
{#if badges.length}
<div bind:this={group} class="student-badges" aria-label="Student highlights">
  {#each badges.slice(0, limit) as badge (badge.id)}
    <button class={`evidence-badge ${badge.tone}`} aria-haspopup="dialog" aria-expanded={active === badge.id}
      onpointerenter={(e) => { if (e.pointerType === 'mouse') show(badge, e.currentTarget); }}
      onpointerleave={(e) => { if(e.pointerType === 'mouse') leave(); }}
      onfocus={(e) => { if(!restoringFocus && e.currentTarget.matches(':focus-visible')) show(badge, e.currentTarget); }}
      onblur={focusLeft} onclick={(e) => show(badge, e.currentTarget)}>{badge.label}</button>
  {/each}
</div>
<Popover.Root open={!!selected} onOpenChange={(open) => { if (!open) active = null; }}>
  <Popover.Portal>
    <Popover.Content bind:ref={content} customAnchor={trigger} class="floating-surface badge-evidence" role="dialog" aria-label={`${selected?.label} evidence`} sideOffset={6} collisionPadding={12}
      onInteractOutside={(e) => { if (e.target instanceof Node && group?.contains(e.target)) e.preventDefault(); }}
      onOpenAutoFocus={(e) => e.preventDefault()}
      onCloseAutoFocus={(e) => { e.preventDefault(); if (content?.contains(document.activeElement)) { restoringFocus = true; trigger?.focus({ preventScroll: true }); queueMicrotask(() => restoringFocus = false); } }}
      onpointerenter={() => clearTimeout(timer)} onpointerleave={leave} onfocusout={focusLeft}>
      {#if selected}
        <div class="badge-evidence-heading"><strong>{selected.label}</strong><Popover.Close aria-label="Close badge evidence" class="badge-close"><X size={14} /></Popover.Close></div>
        <p>{selected.evidence}</p>
        {#each selected.sources as source}{#if source.href.startsWith('/') || safeUrl(source.href)}<a href={source.href} onclick={() => active = null}>{source.label} ↗</a>{/if}{/each}
      {/if}
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>
{/if}
<style>
  .student-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
  .evidence-badge { display: inline-flex; align-items: center; border: 0; border-radius: 4px; padding: 3px 7px; font: 12px/1.5 var(--font-sans); white-space: nowrap; background: var(--surface); color: var(--muted); }
  .positive { color: var(--positive); background: color-mix(in srgb, var(--positive) 9%, var(--bg)); }
  .negative { color: var(--negative); background: color-mix(in srgb, var(--negative) 8%, var(--bg)); }
  .caution { color: light-dark(#805b0b, #e4bc62); background: light-dark(#f2ead8, #3a3020); }
  .evidence-badge:focus-visible { outline: 1px solid currentColor; outline-offset: 2px; }
  :global(.badge-evidence) {width: min(340px, calc(100vw - 24px)); max-height: var(--bits-popover-content-available-height); overflow: auto; padding: 16px; font: 13px/1.65 var(--font-sans); }
  .badge-evidence-heading { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  :global(.badge-close) { padding: 3px; border: 0; background: transparent; color: var(--muted); }
  .badge-evidence-heading strong { font-weight: 500; }
  p { margin: 10px 0; }
  a { display: block; margin-top: 6px; }
</style>
