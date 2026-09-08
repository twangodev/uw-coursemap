<script lang="ts">
  import { Select } from "bits-ui";
  import { Check, ChevronDown } from "@lucide/svelte";
  let { value = $bindable(""), options, label, onChange }: {
    value?: string;
    options: { value: string; label: string }[];
    label: string;
    onChange?: (value: string) => void;
  } = $props();
</script>

<Select.Root type="single" value={value || "__all"} onValueChange={(next) => { value = next === "__all" ? "" : next; onChange?.(value); }}>
  <Select.Trigger class="course-select-trigger" aria-label={label}>
    <span>{options.find((option) => option.value === value)?.label || label}</span><ChevronDown size={14} />
  </Select.Trigger>
  <Select.Portal>
    <Select.Content class="course-select-content" sideOffset={5}>
      <Select.Viewport>
        {#each options as option}
          <Select.Item value={option.value || "__all"} label={option.label} class="course-select-item">
            {#snippet children({ selected })}
              <span>{option.label}</span>{#if selected}<Check size={14} />{/if}
            {/snippet}
          </Select.Item>
        {/each}
      </Select.Viewport>
    </Select.Content>
  </Select.Portal>
</Select.Root>

<style>
  :global(.course-select-trigger) { display: inline-flex; align-items: center; justify-content: space-between; gap: 16px; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 5px; padding: 9px 12px; font: inherit; font-size: 13px; max-width: 100%; cursor: pointer; }
  :global(.course-select-trigger span) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  :global(.course-select-trigger svg) { flex-shrink: 0; color: var(--muted); }
  :global(.course-select-trigger:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
  :global(.course-select-content) { z-index: 100; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 4px; box-shadow: 0 8px 24px #0002; min-width: var(--bits-select-anchor-width); max-width: min(360px, calc(100vw - 24px)); max-height: min(320px, var(--bits-select-content-available-height)); overflow-y: auto; }
  :global(.course-select-item) { display: flex; align-items: center; justify-content: space-between; gap: 20px; border-radius: 3px; padding: 9px 10px; font-size: 13px; cursor: pointer; outline: none; }
  :global(.course-select-item[data-highlighted]) { background: var(--border); }
  :global(.course-select-item svg) { flex-shrink: 0; color: var(--accent); }
</style>
