<script lang="ts">

    import {cn} from "$lib/utils.ts";
    import {onMount} from "svelte";

    interface Props {
        clampAmount: number,
        class?: string,
        children?: () => any
    }

    let { clampAmount, class: className = '', children }: Props = $props();

    let element: HTMLParagraphElement
    let showToggle = $state(false);
    let expanded = $state(false);

    function checkOverflow() {
        if (!element) return;
        showToggle = element.scrollHeight > element.clientHeight;
    }

    function toggleExpand() {
        expanded = !expanded;
    }

    onMount(() => {
        checkOverflow();
        window.addEventListener('resize', checkOverflow);
    })

    $effect(() => {
        checkOverflow();
    });

</script>

<div>
    <p class={cn(className, expanded ? "line-clamp-none" : `line-clamp-${clampAmount}`)} bind:this={element}>
        {@render children?.()}
    </p>
    {#if showToggle}
        <button
            onclick={toggleExpand}
            class="mt-1 text-xs font-medium text-muted-foreground hover:underline"
        >
            Show {expanded ? "Less" : "More"}
        </button>
    {/if}
</div>

