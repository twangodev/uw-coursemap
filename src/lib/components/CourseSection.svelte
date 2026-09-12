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

<section {id} class={`panel ${className}`} class:facts={layout === "facts"}>
  <div class="panel-heading">
    <h2>{title}</h2>
    {#if tools}{@render tools()}{:else if label}<span class="mono muted"
        >{label}</span
      >{/if}
  </div>
  <div class="panel-body">{@render children()}</div>
</section>

<style>
  .panel {
    min-width: 0;
    scroll-margin-top: calc(var(--course-navigation-height, 43px) + 32px);
  }
  .panel-heading {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    position: sticky;
    top: var(--course-navigation-height, 43px);
    z-index: 10;
    padding: 20px 0;
    background: var(--bg);
  }
  h2 {
    font-size: 28px;
    font-weight: 500;
    letter-spacing: -0.01em;
  }
  .panel-heading .mono {
    font-size: 12px;
  }
  .panel-body {
    min-width: 0;
  }
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
