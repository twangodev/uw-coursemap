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

<div class="term-picker" role="group" aria-label={groupLabel}>
  <button
    aria-label={value ? "Previous term" : "Latest term"}
    disabled={!ordered.length || index >= ordered.length - 1}
    onclick={() => onChange(ordered[index + 1])}
    ><ChevronLeft size={14} /></button
  >
  <Select {label} {value} {options} {onChange} />
  <button
    aria-label="Next term"
    disabled={index <= 0}
    onclick={() => onChange(ordered[index - 1])}
    ><ChevronRight size={14} /></button
  >
</div>

<style>
  .term-picker {
    display: inline-grid;
    grid-template-columns: 28px minmax(0, 1fr) 28px;
    max-width: 100%;
    height: 30px;
    border: 1px solid var(--border);
    border-radius: var(--radius-control, 5px);
    background: var(--surface);
  }
  .term-picker :global(.course-select-trigger) {
    height: 28px;
    border: 0;
    border-inline: 1px solid var(--border);
    border-radius: 0;
    background: transparent;
    padding-block: 0;
  }
  button {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    color: var(--muted);
  }
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
