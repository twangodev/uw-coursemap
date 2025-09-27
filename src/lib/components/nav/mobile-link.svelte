<script lang="ts">
  import { page } from "$app/state";
  import { cn } from "$lib/utils.js";
  import { localizeHref } from "$lib/paraglide/runtime";

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

  const localizedHref = $derived(href.startsWith('http') ? href : localizeHref(href));
</script>

<a
  href={localizedHref}
  class={cn(
    page.url.pathname === localizedHref ? "text-foreground" : "text-foreground/60",
    className,
  )}
  onclick={() => (open = false)}
  {...rest}
>
  {@render children?.()}
</a>
