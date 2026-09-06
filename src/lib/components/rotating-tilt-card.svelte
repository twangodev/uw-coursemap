<script lang="ts">
  import { Code, Database, Waypoints, Upload } from "@lucide/svelte";
  import { inView } from "$lib/actions/in-view";
  import { m } from "$lib/paraglide/messages";

  const DISPLAY_DURATION = 5000;

  const cardImages = ["/compsci-300.webp", "/compsci-graph.webp"];

  let i = $state(0);
  let cardVisible = $state(false);
  let cardElement = $state<HTMLElement | undefined>(undefined);

  $effect(() => {
    if (!cardElement) return;
    const observer = new IntersectionObserver(([entry]) => {
      cardVisible = entry.isIntersecting;
    });
    observer.observe(cardElement);
    return () => observer.disconnect();
  });

  $effect(() => {
    if (!cardVisible) return;
    const interval = setInterval(() => {
      i = (i + 1) % cardImages.length;
    }, DISPLAY_DURATION);

    return () => {
      clearInterval(interval);
    };
  });

  function toDarkVariant(url: string): string {
    return url.replace(/\.\w+$/, "") + "-dark.webp";
  }
</script>

<div
  bind:this={cardElement}
  class="mx-auto -mt-16 max-w-7xl overflow-hidden contain-paint lg:pr-44"
>
  <div class="-mr-16 perspective-distant lg:-mr-56 lg:pl-32">
    <div class="[transform:rotateX(20deg);]">
      <div class="relative skew-x-[.25rad] lg:h-176">
        <div
          aria-hidden="true"
          class="absolute -inset-16 z-1 bg-[url(/hero-decor-light.svg)] bg-no-repeat [background-size:100%_100%] sm:-inset-32 dark:hidden"
        ></div>
        <div
          aria-hidden="true"
          class="absolute -inset-16 z-1 hidden bg-[url(/hero-decor-dark.svg)] bg-no-repeat [background-size:100%_100%] sm:-inset-32 dark:block"
        ></div>
        <div
          aria-hidden="true"
          class="absolute inset-0 z-11 bg-[url(/hero-overlay-light.svg)] bg-no-repeat [background-size:100%_100%] dark:hidden"
        ></div>
        <div
          aria-hidden="true"
          class="absolute inset-0 z-11 hidden bg-[url(/hero-overlay-dark.svg)] bg-no-repeat [background-size:100%_100%] dark:block"
        ></div>
        <div class="mt-8 mb-8 grid">
          {#each cardImages as image, index}
            <div
              class="z-1 col-start-1 row-start-1 mx-auto rounded-(--radius) border-3 transition-opacity duration-700 ease-in-out dark:border {index ===
              i
                ? 'opacity-100'
                : 'opacity-0'}"
            >
              <img
                class="rounded-(--radius) dark:hidden"
                src={image}
                alt="Preview"
                width="1920"
                height="1080"
                decoding="async"
              />
              <img
                class="hidden rounded-(--radius) dark:block"
                src={toDarkVariant(image)}
                alt="Preview"
                width="1920"
                height="1080"
                decoding="async"
              />
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</div>
<div class="mx-auto mt-4 max-w-5xl space-y-12 px-6">
  <div
    class="relative mx-auto grid grid-cols-2 gap-x-3 gap-y-6 sm:gap-8 lg:grid-cols-4"
  >
    <div use:inView={{ threshold: 0.3, once: true }} class="space-y-3 opacity-0 scale-95 transition-[opacity,transform] duration-500 [&.in-view]:opacity-100 [&.in-view]:scale-100">
      <div class="flex items-center gap-2">
        <Upload class="size-4" />
        <h3 class="text-sm font-medium">{m["home.features.upload.title"]()}</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        {m["home.features.upload.description"]()}
      </p>
    </div>
    <div use:inView={{ threshold: 0.3, once: true }} class="space-y-2 opacity-0 scale-95 transition-[opacity,transform] duration-500 delay-100 [&.in-view]:opacity-100 [&.in-view]:scale-100">
      <div class="flex items-center gap-2">
        <Waypoints class="size-4" />
        <h3 class="text-sm font-medium">{m["home.features.visualFirst.title"]()}</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        {m["home.features.visualFirst.description"]()}
      </p>
    </div>
    <div use:inView={{ threshold: 0.3, once: true }} class="space-y-2 opacity-0 scale-95 transition-[opacity,transform] duration-500 delay-200 [&.in-view]:opacity-100 [&.in-view]:scale-100">
      <div class="flex items-center gap-2">
        <Code class="size-4" />
        <h3 class="text-sm font-medium">{m["home.features.openSource.title"]()}</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        {m["home.features.openSource.description"]()}
      </p>
    </div>
    <div use:inView={{ threshold: 0.3, once: true }} class="space-y-2 opacity-0 scale-95 transition-[opacity,transform] duration-500 delay-300 [&.in-view]:opacity-100 [&.in-view]:scale-100">
      <div class="flex items-center gap-2">
        <Database class="size-4" />
        <h3 class="text-sm font-medium">{m["home.features.dataFriendly.title"]()}</h3>
      </div>
      <p class="text-muted-foreground text-sm">
        {m["home.features.dataFriendly.description"]()}
      </p>
    </div>
  </div>
</div>

