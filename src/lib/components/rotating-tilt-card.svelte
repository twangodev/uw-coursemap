<script lang="ts">

    import {slide, type SlideParams} from "svelte/transition";
    import {quadInOut} from "svelte/easing";

    const DISPLAY_DURATION = 5000

    const cardImages = [
        '/compsci-300.png',
        '/compsci-graph.png'
    ]

    let i = $state(0)

    $effect(() => {
        const interval = setInterval(() => {
            i = (i + 1) % cardImages.length;
        }, DISPLAY_DURATION);

        return () => {
            clearInterval(interval);
        };
    });

    function toDarkVariant(url: string): string {
        return url.endsWith('.png')
            ? url.slice(0, -4) + '-dark.png'
            : url.replace(/\.\w+$/, '') + '-dark.png';
    }

    const slideParams: SlideParams = {
        duration: 750,
        easing: quadInOut,
        axis: "y",
    }


</script>

<div class="overflow-hidden -mt-16 mx-auto max-w-7xl lg:pr-44">
    <div class="perspective-distant -mr-16 lg:-mr-56 lg:pl-32">
        <div class="[transform:rotateX(20deg);]">
            <div class="lg:h-176 relative skew-x-[.25rad]">
                <div aria-hidden="true" class="bg-linear-to-b from-background to-background z-1 absolute -inset-16 via-transparent sm:-inset-32"></div>
                <div aria-hidden="true" class="bg-linear-to-r from-background to-background z-1 absolute -inset-16 bg-white/50 via-transparent sm:-inset-32 dark:bg-transparent"></div>
                <div aria-hidden="true" class="absolute -inset-16 bg-[linear-gradient(to_right,var(--color-border)_1px,transparent_1px),linear-gradient(to_bottom,var(--color-border)_1px,transparent_1px)] bg-[size:24px_24px] [--color-border:var(--color-black)] sm:-inset-32 dark:[--color-border:color-mix(in_oklab,var(--color-white)_50%,transparent)]"></div>
                <div aria-hidden="true" class="from-background/20 dark:from-background/60 z-11 absolute inset-0 bg-gradient-to-l"></div>
                <div aria-hidden="true" class="z-2 absolute inset-0 size-full items-center px-5 py-24 [background:radial-gradient(125%_125%_at_50%_10%,transparent_40%,var(--color-background)_100%)]"></div>
                <div aria-hidden="true" class="z-2 absolute inset-0 size-full items-center px-5 py-24 [background:radial-gradient(125%_125%_at_50%_10%,transparent_40%,var(--color-background)_100%)]"></div>
                <div class="mt-8 mb-8">
                    {#key cardImages[i]}
                        <div class="rounded-(--radius) z-1 relative border-3 dark:border mx-auto" transition:slide={slideParams}>
                            <img
                                    class="rounded-(--radius) z-1 relative dark:hidden"
                                    src={cardImages[i]}
                                    alt="COMPSCI 300 Preview"
                                    width=3840
                                    height=2160
                            />
                            <img
                                    class="rounded-(--radius) z-1 relative hidden dark:block"
                                    src={toDarkVariant(cardImages[i])}
                                    alt="COMPSCI 300 Preview"
                                    width=3840
                                    height=2160
                            />
                        </div>
                    {/key}
                </div>
            </div>
        </div>
    </div>
</div>
