<script lang="ts">
  import { page } from "$app/state";
  import { cn } from "$lib/utils.js";

  interface Props {
    href: string;
    open: boolean;
    class?: string | undefined | null;
    children?: import("svelte").Snippet;
    [key: string]: any;
  }

  let {
    href,
    open = $bindable(),
    class: className = undefined,
    children,
    ...rest
  }: Props = $props();
</script>

<a
  {href}
  class={cn(
    page.url.pathname === href ? "text-foreground" : "text-foreground/60",
    className,
  )}
  onclick={() => (open = false)}
  {...rest}
>
  {@render children?.()}
</a>
