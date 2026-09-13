<script lang="ts">
  import InfoTooltip from "./InfoTooltip.svelte";
  import { Cpu } from "@lucide/svelte";
  import {
    resolveModelPublisher,
    type ModelPublisher,
  } from "$lib/model-identity";
  let {
    model,
    revision,
    label = "AI disclaimer",
    description = "",
  }: {
    model?: string | null;
    revision?: string | null;
    label?: string;
    description?: string;
  } = $props();
  let open = $state(false);
  let publisher = $state<ModelPublisher | null>(null);
  let imageFailed = $state(false);
  $effect(() => {
    const currentModel = model;
    publisher = null;
    imageFailed = false;
    if (!open) return;
    let cancelled = false;
    resolveModelPublisher(currentModel).then((value) => {
      if (!cancelled) publisher = value;
    });
    return () => {
      cancelled = true;
    };
  });
</script>

<InfoTooltip
  triggerClass="ai-disclaimer info-trigger"
  {label}
  bind:open
  contentClass="ai-disclaimer-tooltip"
>
  <div class="flex items-center gap-[9px] wrap-anywhere model-identity">
    {#if publisher?.avatar && !imageFailed}<img
        class="w-5 h-5 shrink-0 rounded-[3px]"
        src={publisher.avatar}
        alt={publisher.name}
        width="20"
        height="20"
        referrerpolicy="no-referrer"
        onerror={() => (imageFailed = true)}
      />{:else}<Cpu size={18} aria-hidden="true" />{/if}
    <span class="min-w-0">{model || "Model not recorded"}</span>
  </div>
  <p class="mt-2.5 mb-0 text-muted mx-0">
    AI-generated content may be inaccurate. Check the linked sources and
    official catalog.
  </p>
  {#if description}<p class="mt-2.5 mb-0 text-muted mx-0">{description}</p>{/if}
  {#if revision}<p
      class="mt-2.5 mb-0 text-muted text-[11px] wrap-anywhere model-revision mx-0"
    >
      Model revision: {revision}
    </p>{/if}
</InfoTooltip>

<style>
  img {
    object-fit: contain;
  }
</style>
