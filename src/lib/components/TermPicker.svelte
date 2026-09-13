<script lang="ts">
  import { ChevronLeft, ChevronRight } from "@lucide/svelte";
  import Select from "./Select.svelte";
  import { termName } from "$lib/format";
  let {
    terms,
    value,
    label = "Term",
    groupLabel = label,
    all = false,
    projected = "",
    onChange,
  }: {
    terms: string[];
    value: string;
    label?: string;
    groupLabel?: string;
    all?: boolean;
    projected?: string;
    onChange: (term: string) => void;
  } = $props();
  const ordered = $derived(
    [...new Set(terms)].filter(Boolean).sort().reverse(),
  );
  const index = $derived(ordered.indexOf(value));
  const options = $derived([
    ...(all ? [{ value: "", label: "All recorded terms" }] : []),
    ...ordered.map((term) => ({
      value: term,
      label: termName(term) + (term === projected ? " · Projected" : ""),
    })),
  ]);
</script>

<div
  class="inline-grid grid-cols-[28px_minmax(0,_1fr)_28px] max-w-full h-7.5 border border-border rounded-[var(--radius-control,_5px)] bg-surface term-picker"
  role="group"
  aria-label={groupLabel}
>
  <button
    class="grid place-items-center w-7 h-7 p-0 border-0 rounded-none bg-transparent text-muted"
    aria-label={value ? "Previous term" : "Latest term"}
    disabled={!ordered.length || index >= ordered.length - 1}
    onclick={() => onChange(ordered[index + 1])}
    ><ChevronLeft size={14} /></button
  >
  <Select variant="segmented" {label} {value} {options} {onChange} />
  <button
    class="grid place-items-center w-7 h-7 p-0 border-0 rounded-none bg-transparent text-muted"
    aria-label="Next term"
    disabled={index <= 0}
    onclick={() => onChange(ordered[index - 1])}
    ><ChevronRight size={14} /></button
  >
</div>

<style>
  button:first-child {
    border-radius: 4px 0 0 4px;
  }
  button:last-child {
    border-radius: 0 4px 4px 0;
  }
  button:hover:not(:disabled) {
    background: var(--border);
    color: var(--text);
  }
  button:disabled {
    opacity: 0.3;
  }
  button:focus-visible {
    outline-offset: 2px;
  }
</style>
