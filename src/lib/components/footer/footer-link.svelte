<script lang="ts">
  interface Props {
    href?: string;
    target?: string;
    className?: string;
    children?: import("svelte").Snippet;
  }

  let {
    href = "",
    target = "_blank",
    className = "font-medium underline underline-offset-4",
    children,
  }: Props = $props();
</script>

<a {href} {target} class={className}>
  {@render children?.()}
</a>
