<script lang="ts">
  import InfoTooltip from "./InfoTooltip.svelte";
  import { Cpu } from '@lucide/svelte';
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
<InfoTooltip triggerClass="ai-disclaimer info-trigger" {label} bind:open contentClass="ai-disclaimer-tooltip">
    <div class="model-identity">
      {#if publisher?.avatar && !imageFailed}<img src={publisher.avatar} alt={publisher.name} width="20" height="20" referrerpolicy="no-referrer" onerror={() => imageFailed = true} />{:else}<Cpu size={18} aria-hidden="true" />{/if}
      <span>{model || 'Model not recorded'}</span>
    </div>
    <p>AI-generated content may be inaccurate. Check the linked sources and official catalog.</p>
    {#if description}<p>{description}</p>{/if}
    {#if revision}<p class="model-revision">Model revision: {revision}</p>{/if}
</InfoTooltip>
<style>
  .model-identity { display: flex; align-items: center; gap: 9px; overflow-wrap: anywhere; }
  .model-identity span { min-width: 0; }
  img { width: 20px; height: 20px; flex-shrink: 0; object-fit: contain; border-radius: 3px; }
  p { margin: 10px 0 0; color: var(--muted); }
  .model-revision { font-size: 11px; overflow-wrap: anywhere; }
</style>
