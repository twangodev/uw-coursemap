<script lang="ts">
  import { Select } from "bits-ui";
  import { Check, ChevronDown } from "@lucide/svelte";
  let {
    value = $bindable(""),
    options,
    label,
    onChange,
    variant = "default",
    width = "auto",
  }: {
    value?: string;
    options: { value: string; label: string }[];
    label: string;
    onChange?: (value: string) => void;
    variant?: "default" | "compact" | "segmented";
    width?: "auto" | "filter";
  } = $props();

  const variants = {
    default: "border border-border rounded-control bg-surface py-1",
    compact:
      "h-7.5 box-border border border-border rounded-control bg-surface py-0",
    segmented:
      "h-7 border-0 border-x border-border rounded-none bg-transparent py-0",
  };
</script>

<Select.Root
  type="single"
  value={value || "__all"}
  onValueChange={(next) => {
    value = next === "__all" ? "" : next;
    onChange?.(value);
  }}
>
  <Select.Trigger
    class={`course-select-trigger inline-flex items-center justify-between gap-4 px-2.5 text-[12px] leading-[18px] text-foreground cursor-pointer focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2 ${variants[variant]} ${width === "filter" ? "max-w-60 [@media(max-width:600px)]:max-w-full" : "max-w-full"}`}
    aria-label={label}
  >
    <span class="truncate"
      >{options.find((option) => option.value === value)?.label || label}</span
    >
    <ChevronDown size={14} class="shrink-0 text-muted" />
  </Select.Trigger>
  <Select.Portal>
    <Select.Content
      class="course-select-content z-100 min-w-(--bits-select-anchor-width) max-w-[min(360px,calc(100vw-24px))] max-h-[min(320px,var(--bits-select-content-available-height))] overflow-y-auto rounded-[6px] border border-border bg-surface p-1 text-foreground shadow-[0_8px_24px_#0002]"
      sideOffset={5}
    >
      <Select.Viewport>
        {#each options as option}
          <Select.Item
            value={option.value || "__all"}
            label={option.label}
            class="course-select-item flex cursor-pointer items-center justify-between gap-5 rounded-[3px] px-[9px] py-[5px] text-[12px] leading-[18px] outline-none data-highlighted:bg-border"
          >
            {#snippet children({ selected })}
              <span>{option.label}</span>
              {#if selected}<Check
                  size={14}
                  class="shrink-0 text-accent"
                />{/if}
            {/snippet}
          </Select.Item>
        {/each}
      </Select.Viewport>
    </Select.Content>
  </Select.Portal>
</Select.Root>
