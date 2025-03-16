<script lang="ts">
    import { LockKeyhole, LockKeyholeOpen, LucideFullscreen, LucideMinus, LucidePlus } from "lucide-svelte";
    import { Button } from "../ui/button";
    import IconTooltipStateWrapper from "../icon-toolips/icon-tooltip-state-wrapper.svelte";
    import IconTootipWrapper from "../icon-toolips/icon-tootip-wrapper.svelte";

    let { elementsAreDraggable = $bindable<boolean>(), cy } = $props();

    let isFullscreen = $state(false);

    const toggleFullscreen = () => {
        if (!isFullscreen) {
            let element = document.getElementById('cy-container');
            element?.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
        isFullscreen = !isFullscreen;
    };

    const zoomIn = () => {
        cy?.zoom(cy.zoom() + 0.1);
    };

    const zoomOut = () => {
        cy?.zoom(cy.zoom() - 0.1);
    };

    const toggleDraggableElements = () => {
        elementsAreDraggable = !elementsAreDraggable;
    }

</script>
<div class="absolute bottom-4 right-4 flex flex-col space-y-2">

    <IconTooltipStateWrapper
            state={elementsAreDraggable}
            onclick={toggleDraggableElements}
            activeTooltip="Lock Elements"
            inactiveTooltip="Unlock Elements"
    >
        {#snippet active()}
            <LockKeyholeOpen class="h-5 w-5" />
        {/snippet}
        {#snippet inactive()}
            <LockKeyhole class="h-5 w-5" />
        {/snippet}
    </IconTooltipStateWrapper>

    <IconTootipWrapper tooltip="Zoom In" onclick={zoomIn}>
        <LucidePlus class="h-5 w-5"/>
    </IconTootipWrapper>

    <IconTootipWrapper tooltip="Zoom Out" onclick={zoomOut}>
        <LucideMinus class="h-5 w-5"/>
    </IconTootipWrapper>

    <IconTootipWrapper tooltip="Fullscreen" onclick={toggleFullscreen}>
        <LucideFullscreen class="h-5 w-5"/>
    </IconTootipWrapper>

</div>