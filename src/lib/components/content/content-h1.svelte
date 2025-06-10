<script lang="ts">
  interface Props {
    children?: import("svelte").Snippet;
  }

  let { children }: Props = $props();
</script>

<h1 class="scroll-m-20 text-4xl font-bold tracking-tight">
  {@render children?.()}
</h1>
