<script lang="ts">
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import type { WithoutChildren } from "bits-ui";
  import { getEmblaContext } from "./context.js";
  import { cn } from "$lib/utils.js";
  import { Button, type Props } from "$lib/components/ui/button/index.js";

  let {
    ref = $bindable(null),
    class: className,
    variant = "outline",
    size = "icon",
    ...restProps
  }: WithoutChildren<Props> = $props();

  const emblaCtx = getEmblaContext("<Carousel.Previous/>");
</script>

<div
  class={cn(
    "transition-opacity",
    emblaCtx.canScrollPrev ? "opacity-100" : "opacity-0",
  )}
>
  <Button
    {variant}
    {size}
    class={cn(
      "absolute size-8 touch-manipulation rounded-full",
      emblaCtx.orientation === "horizontal"
        ? "top-1/2 left-2 -translate-y-1/2"
        : "-top-12 left-1/2 -translate-x-1/2 rotate-90",
      className,
    )}
    disabled={!emblaCtx.canScrollPrev}
    onclick={emblaCtx.scrollPrev}
    onkeydown={emblaCtx.handleKeyDown}
    {...restProps}
    bind:ref
  >
    <ArrowLeft class="size-4" />
    <span class="sr-only">Previous slide</span>
  </Button>
</div>
