<script lang="ts">
  import type { Snippet } from "svelte";
  let {
    title,
    id,
    label,
    class: className = "",
    children,
    tools,
  }: {
    title: string;
    id?: string;
    label?: string;
    class?: string;
    children: Snippet;
    tools?: Snippet;
  } = $props();
</script>

<section {id} class={`panel ${className}`}>
  <div class="panel-heading">
    <h2>{title}</h2>
    {#if tools}{@render tools()}{:else if label}<span class="mono muted"
        >{label}</span
      >{/if}
  </div>
  <div class="panel-body">{@render children()}</div>
</section>
