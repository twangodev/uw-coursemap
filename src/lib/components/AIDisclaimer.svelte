<script lang="ts">
  import { Tooltip } from 'bits-ui';
  import { Info, Cpu } from '@lucide/svelte';
  import { resolveModelPublisher, type ModelPublisher } from '$lib/model-identity';
  let { model, revision, label = 'AI disclaimer', description = '' }: { model?: string | null; revision?: string | null; label?: string; description?: string } = $props();
  let open = $state(false);
  let publisher = $state<ModelPublisher | null>(null);
  let imageFailed = $state(false);
  $effect(() => {
    const currentModel = model;
    publisher = null;
    imageFailed = false;
    if (!open) return;
    let cancelled = false;
    resolveModelPublisher(currentModel).then(value => { if (!cancelled) publisher = value; });
    return () => { cancelled = true; };
  });
</script>
<Tooltip.Provider delayDuration={150}><Tooltip.Root bind:open disableCloseOnTriggerClick>
  <Tooltip.Trigger class="ai-disclaimer" aria-label={label} onclick={() => open = true}><Info size={14} /></Tooltip.Trigger>
  <Tooltip.Portal><Tooltip.Content class="ai-disclaimer-tooltip" role="tooltip" sideOffset={6} collisionPadding={12}>
    <div class="model-identity">
      {#if publisher?.avatar && !imageFailed}<img src={publisher.avatar} alt={publisher.name} width="20" height="20" referrerpolicy="no-referrer" onerror={() => imageFailed = true} />{:else}<Cpu size={18} aria-hidden="true" />{/if}
      <span>{model || 'Model not recorded'}</span>
    </div>
    <p>AI-generated content may be inaccurate. Check the linked sources and official catalog.</p>
    {#if description}<p>{description}</p>{/if}
    {#if revision}<p class="model-revision">Model revision: {revision}</p>{/if}
  </Tooltip.Content></Tooltip.Portal>
</Tooltip.Root></Tooltip.Provider>
<style>
  :global(.ai-disclaimer) { display: inline-flex; align-items: center; padding: 2px; border: 0; background: transparent; color: var(--muted); cursor: help; }
  :global(.ai-disclaimer-tooltip) { z-index: 100; width: min(340px, calc(100vw - 24px)); padding: 14px 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text); font: 13px/1.65 var(--font-sans); box-shadow: 0 8px 24px #0002; }
  .model-identity { display: flex; align-items: center; gap: 9px; overflow-wrap: anywhere; }
  .model-identity span { min-width: 0; }
  img { width: 20px; height: 20px; flex-shrink: 0; object-fit: contain; border-radius: 3px; }
  p { margin: 10px 0 0; color: var(--muted); }
  .model-revision { font-size: 11px; overflow-wrap: anywhere; }
</style>
