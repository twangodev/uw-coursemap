<script lang="ts">
  import { Tooltip } from 'bits-ui';
  import { Info, Cpu } from '@lucide/svelte';
  import { modelFamily } from '$lib/model-identity';
  let { model, revision }: { model?: string | null; revision?: string | null } = $props();
  let open = $state(false);
</script>
<Tooltip.Provider delayDuration={150}><Tooltip.Root bind:open disableCloseOnTriggerClick>
  <Tooltip.Trigger class="ai-info" aria-label="About AI suggestions" onclick={() => open = true}><Info size={14} /></Tooltip.Trigger>
  <Tooltip.Portal><Tooltip.Content class="ai-info-tooltip" role="tooltip" sideOffset={6} collisionPadding={12}>
    <div class="model-identity">
      {#if modelFamily(model) === 'qwen'}<span role="img" aria-label="Qwen" class="model-logo"></span>{:else}<Cpu size={18} aria-hidden="true" />{/if}
      <span>{model || 'Model not recorded'}</span>
    </div>
    <p>AI-suggested background, not official prerequisites. Check the catalog requirements.</p>
    {#if revision}<p class="model-revision">Model revision: {revision}</p>{/if}
  </Tooltip.Content></Tooltip.Portal>
</Tooltip.Root></Tooltip.Provider>
<style>
  :global(.ai-info) { display: inline-flex; align-items: center; padding: 2px; border: 0; background: transparent; color: var(--muted); cursor: help; }
  :global(.ai-info-tooltip) { z-index: 100; width: min(340px, calc(100vw - 24px)); padding: 14px 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text); font: 13px/1.65 var(--font-sans); box-shadow: 0 8px 24px #0002; }
  .model-identity { display: flex; align-items: center; gap: 9px; overflow-wrap: anywhere; }
  .model-identity > span:last-child { min-width: 0; }
  .model-logo { width: 20px; height: 20px; flex-shrink: 0; background: currentColor; mask-image: url("../assets/models/qwen.svg"); mask-size: contain; mask-repeat: no-repeat; }
  p { margin: 10px 0 0; color: var(--muted); }
  .model-revision { font-size: 11px; overflow-wrap: anywhere; }
</style>
