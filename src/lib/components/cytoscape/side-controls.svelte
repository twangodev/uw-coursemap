<script lang="ts">
    import { LockKeyhole, LockKeyholeOpen, LucideFullscreen, LucideMinus, LucidePlus } from "lucide-svelte";
    import { Button } from "../ui/button";
    import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";

    let { elementsAreDraggable = $bindable<boolean>(), cy } = $props();

    let isFullscreen = false;
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
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger>
                    <Button size="sm" variant="outline" class="h-8 w-8 px-0" onclick={toggleDraggableElements}>
                        {#if elementsAreDraggable}
                            <LockKeyholeOpen class="h-5 w-5" />
                        {:else}
                            <LockKeyhole class="h-5 w-5"/>
                        {/if}
                    </Button>
                </TooltipTrigger>
                <TooltipContent>
                    {#if elementsAreDraggable}
                        Lock Elements
                    {:else}
                        Unlock Elements
                    {/if}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>

        <Button size="sm" variant="outline" class="h-8 w-8 px-0" onclick={zoomIn}>
            <LucidePlus class="h-5 w-5"/>
        </Button>
        <!-- Zoom Out Button -->
        <Button  size="sm" variant="outline" class="h-8 w-8 px-0" onclick={zoomOut}>
            <LucideMinus class="h-5 w-5"/>
        </Button>

        <Button  size="sm" variant="outline" class="h-8 w-8 px-0" onclick={toggleFullscreen}>
            <LucideFullscreen class="h-5 w-5"/>
        </Button>
    </div>