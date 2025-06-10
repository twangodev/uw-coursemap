<script lang="ts">
  import { slide, type SlideParams } from "svelte/transition";
  import { quadInOut } from "svelte/easing";
  import { Code, Database, Waypoints, Upload } from "@lucide/svelte";

  const DISPLAY_DURATION = 5000;

  const cardImages = ["/compsci-300.png", "/compsci-graph.png"];

  let i = $state(0);

  $effect(() => {
    const interval = setInterval(() => {
      i = (i + 1) % cardImages.length;
    }, DISPLAY_DURATION);

    return () => {
      clearInterval(interval);
    };
  });

  function toDarkVariant(url: string): string {
    return url.endsWith(".png")
      ? url.slice(0, -4) + "-dark.png"
      : url.replace(/\.\w+$/, "") + "-dark.png";
  }

  const slideParams: SlideParams = {
    duration: 750,
    easing: quadInOut,
    axis: "y",
  };
</script>

<div class="mx-auto -mt-16 max-w-7xl overflow-hidden lg:pr-44">
  <div class="-mr-16 perspective-distant lg:-mr-56 lg:pl-32">
    <div class="[transform:rotateX(20deg);]">
      <div class="relative skew-x-[.25rad] lg:h-176">
        <div
          aria-hidden="true"
          class="from-background to-background absolute -inset-16 z-1 bg-linear-to-b via-transparent sm:-inset-32"
        ></div>
        <div
          aria-hidden="true"
          class="from-background to-background absolute -inset-16 z-1 bg-white/50 bg-linear-to-r via-transparent sm:-inset-32 dark:bg-transparent"
        ></div>
        <div
          aria-hidden="true"
          class="absolute -inset-16 bg-[linear-gradient(to_right,var(--color-border)_1px,transparent_1px),linear-gradient(to_bottom,var(--color-border)_1px,transparent_1px)] bg-[size:24px_24px] [--color-border:var(--color-black)] sm:-inset-32 dark:[--color-border:color-mix(in_oklab,var(--color-white)_50%,transparent)]"
        ></div>
        <div
          aria-hidden="true"
          class="from-background/20 dark:from-background/60 absolute inset-0 z-11 bg-gradient-to-l"
        ></div>
        <div
          aria-hidden="true"
          class="absolute inset-0 z-2 size-full items-center px-5 py-24 [background:radial-gradient(125%_125%_at_50%_10%,transparent_40%,var(--color-background)_100%)]"
        ></div>
        <div
          aria-hidden="true"
          class="absolute inset-0 z-2 size-full items-center px-5 py-24 [background:radial-gradient(125%_125%_at_50%_10%,transparent_40%,var(--color-background)_100%)]"
        ></div>
        <div class="mt-8 mb-8">
          {#key cardImages[i]}
            <div
              class="relative z-1 mx-auto rounded-(--radius) border-3 dark:border"
              transition:slide={slideParams}
            >
              <img
                class="relative z-1 rounded-(--radius) dark:hidden"
                src={cardImages[i]}
                alt="Preview"
                width="3840"
                height="2160"
              />
              <img
                class="relative z-1 hidden rounded-(--radius) dark:block"
                src={toDarkVariant(cardImages[i])}
                alt="Preview"
                width="3840"
                height="2160"
              />
            </div>
          {/key}
        </div>
      </div>
    </div>
  </div>
</div>
<div class="mx-auto mt-4 max-w-5xl space-y-12 px-6">
  <div
    class="relative mx-auto grid grid-cols-2 gap-x-3 gap-y-6 sm:gap-8 lg:grid-cols-4"
  >
    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <Upload class="size-4" />
        <h3 class="text-sm font-medium">Upload</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        Upload your transcript to automatically analyze and visualize your
        completed courses.
      </p>
    </div>
    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <Waypoints class="size-4" />
        <h3 class="text-sm font-medium">Visual First</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        View an interactive map of a department and course relationships to
        explore course offerings.
      </p>
    </div>
    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <Code class="size-4" />
        <h3 class="text-sm font-medium">Open Source</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        Built by UW-Madison students, for students. Contribute to our
        open-source project on GitHub.
      </p>
    </div>
    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <Database class="size-4" />
        <h3 class="text-sm font-medium">Data Friendly</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        Download or immediately access our data via API to build your own tools
        and insights.
      </p>
    </div>
  </div>
</div>
