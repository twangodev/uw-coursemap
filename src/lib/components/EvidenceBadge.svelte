<script lang="ts">
  import { Popover } from 'bits-ui';
  import { onDestroy } from 'svelte';
  import { X } from '@lucide/svelte';
  import { safeUrl } from '$lib/format';
  import type { Badge } from '$lib/badges';
  let { badge }: { badge: Badge } = $props();
  let open = $state(false);
  let timer: ReturnType<typeof setTimeout>;
  function keepOpen() { clearTimeout(timer); open = true; }
  function leave() { clearTimeout(timer); timer = setTimeout(() => open = false, 200); }
  onDestroy(() => clearTimeout(timer));
</script>
<Popover.Root bind:open>
  <Popover.Trigger class={`evidence-badge ${badge.tone}`} onpointerenter={(e) => { if(e.pointerType === 'mouse') keepOpen(); }} onpointerleave={(e) => { if(e.pointerType === 'mouse') leave(); }} onfocus={(e) => { if(e.currentTarget.matches(':focus-visible')) keepOpen(); }}>{badge.label}</Popover.Trigger>
  <Popover.Portal>
    <Popover.Content class="badge-evidence" aria-label={`${badge.label} evidence`} sideOffset={6} collisionPadding={12} onOpenAutoFocus={(e) => e.preventDefault()} onpointerenter={keepOpen} onpointerleave={leave}>
      <div class="badge-evidence-heading"><strong>{badge.label}</strong><Popover.Close aria-label="Close badge evidence" class="badge-close"><X size={14} /></Popover.Close></div>
      <p>{badge.evidence}</p>
      {#each badge.sources as source}{#if source.href.startsWith('/') || safeUrl(source.href)}<a href={source.href} onclick={() => open = false}>{source.label} ↗</a>{/if}{/each}
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>
<style>
  :global(.evidence-badge) { display: inline-flex; align-items: center; border: 0; border-radius: 4px; padding: 3px 7px; font: 12px/1.5 var(--font-sans); white-space: nowrap; background: var(--surface); color: var(--muted); }
  :global(.evidence-badge.positive) { color: var(--positive); background: color-mix(in srgb, var(--positive) 9%, var(--bg)); }
  :global(.evidence-badge.negative) { color: var(--negative); background: color-mix(in srgb, var(--negative) 8%, var(--bg)); }
  :global(.evidence-badge.caution) { color: light-dark(#805b0b, #e4bc62); background: light-dark(#f2ead8, #3a3020); }
  :global(.evidence-badge:focus-visible) { outline: 2px solid var(--accent); outline-offset: 3px; }
  :global(.badge-evidence) { z-index: 100; width: min(340px, calc(100vw - 24px)); max-height: var(--bits-popover-content-available-height); overflow: auto; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 16px; box-shadow: 0 8px 30px #0002; font: 13px/1.65 var(--font-sans); }
  .badge-evidence-heading { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  :global(.badge-close) { padding: 3px; border: 0; background: transparent; color: var(--muted); }
  .badge-evidence-heading strong { font-weight: 500; }
  p { margin: 10px 0; }
  a { display: block; margin-top: 6px; }
</style>
