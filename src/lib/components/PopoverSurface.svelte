<script lang="ts">
  import { Popover } from "bits-ui";
  import type { ComponentProps } from "svelte";
  import { floatingSurface } from "./floating-surface";

  let {
    children,
    ref = $bindable(null),
    class: className = "",
    padding = "default",
    width = 340,
    style,
    ...props
  }: ComponentProps<typeof Popover.Content> & {
    width?: number;
    padding?: "none" | "default" | "roomy";
  } = $props();

  const paddingClasses = { none: "p-0", default: "p-4", roomy: "p-5.5" };
</script>

<Popover.Portal>
  <Popover.Content
    bind:ref
    style={`--surface-width: ${width}px; ${style ?? ""}`}
    class={`${floatingSurface} ${paddingClasses[padding]} ${className}`}
    {...props}
  >
    {@render children?.()}
  </Popover.Content>
</Popover.Portal>
