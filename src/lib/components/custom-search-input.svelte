<script lang="ts">
  import Search from "@lucide/svelte/icons/search";
  import { cn } from "$lib/utils.js";
  import { Input } from "./ui/input";

  interface Props {
    class?: string | undefined | null;
    value?: string;
    [key: string]: any;
  }

  let {
    class: className = undefined,
    value = $bindable(""),
    ...rest
  }: Props = $props();
</script>

<div class="flex items-center border-b px-2" data-cmdk-input-wrapper="">
  <Search class="mr-2 h-4 w-4 shrink-0 opacity-50" />
  <Input
    class={cn(
      "placeholder:text-muted-foreground focus-visible:ring-opacity-0 flex h-11 w-full rounded-md border-none bg-transparent py-3 text-sm outline-hidden focus-visible:ring-0 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...rest}
    bind:value
  />
</div>
