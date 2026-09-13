<script lang="ts">
  import type { Snippet } from "svelte";
  let {
    title,
    layout = "section",
    id,
    label,
    class: className = "",
    children,
    tools,
  }: {
    title: string;
    layout?: "section" | "facts";
    id?: string;
    label?: string;
    class?: string;
    children: Snippet;
    tools?: Snippet;
  } = $props();
</script>

<section
  {id}
  class={`min-w-0 [scroll-margin-top:calc(var(--course-navigation-height,_43px)_+_32px)] panel ${className}`}
  class:facts={layout === "facts"}
>
  <div
    class="flex justify-between items-baseline gap-3 sticky top-[var(--course-navigation-height,_43px)] z-10 bg-canvas panel-heading py-5 px-0"
  >
    <h2 class="text-[28px] font-medium tracking-[-0.01em]">{title}</h2>
    {#if tools}{@render tools()}{:else if label}<span
        class="text-[12px] mono muted">{label}</span
      >{/if}
  </div>
  <div class="min-w-0 panel-body">{@render children()}</div>
</section>

<style>
  .panel-body > :global(:last-child) {
    margin-bottom: 0;
  }
  .facts .panel-heading {
    position: static;
    padding: 24px 0;
  }
  .facts h2 {
    font-size: 19px;
    font-weight: 550;
  }
  .facts .panel-body {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 24px 48px;
    font-size: 13px;
  }
  .facts .panel-body > :global(p) {
    grid-column: 1 / -1;
  }
  @media (max-width: 760px) {
    h2 {
      font-size: 24px;
    }
    .facts .panel-body {
      grid-template-columns: 1fr;
      gap: 20px;
    }
  }
</style>
