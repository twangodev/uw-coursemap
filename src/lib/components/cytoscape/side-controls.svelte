<script lang="ts">
  import {
    Group,
    LockKeyhole,
    LockKeyholeOpen,
    LucideFullscreen,
    LucideMinus,
    LucidePlus,
    LucideHash,
    LucideCaseUpper,
    Ungroup,
  } from "@lucide/svelte";
  import IconTooltipStateWrapper from "../icon-toolips/icon-tooltip-state-wrapper.svelte";
  import IconTootipWrapper from "../icon-toolips/icon-tootip-wrapper.svelte";
  import { LayoutType } from "$lib/components/cytoscape/graph-layout.ts";
  import { m } from "$lib/paraglide/messages";

  let {
    elementsAreDraggable = $bindable<boolean>(),
    layoutType = $bindable<LayoutType>(),
    layoutRecompute = () => void LayoutType,
    showCodeLabels = $bindable<boolean>(),
    cy,
  } = $props();

  let isFullscreen = $state(false);

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      let element = document.getElementById("cy-container");
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
  };

  const toggleLayoutType = () => {
    layoutType =
      layoutType === LayoutType.GROUPED
        ? LayoutType.LAYERED
        : LayoutType.GROUPED;
    layoutRecompute(layoutType);
  };

  const toggleShowCodeLabels = () => {
    showCodeLabels = !showCodeLabels;
  };
</script>

<div class="absolute right-4 bottom-4 flex flex-col space-y-2">
  <IconTooltipStateWrapper
    state={showCodeLabels}
    onclick={toggleShowCodeLabels}
    activeTooltip={m["cytoscape.controls.showCourseTitles"]()}
    inactiveTooltip={m["cytoscape.controls.showCourseCodes"]()}
  >
    {#snippet active()}
      <LucideHash class="h-5 w-5" />
    {/snippet}
    {#snippet inactive()}
      <LucideCaseUpper class="h-5 w-5" />
    {/snippet}
  </IconTooltipStateWrapper>

  <IconTooltipStateWrapper
    state={elementsAreDraggable}
    onclick={toggleDraggableElements}
    activeTooltip={m["cytoscape.controls.lockElements"]()}
    inactiveTooltip={m["cytoscape.controls.unlockElements"]()}
  >
    {#snippet active()}
      <LockKeyholeOpen class="h-5 w-5" />
    {/snippet}
    {#snippet inactive()}
      <LockKeyhole class="h-5 w-5" />
    {/snippet}
  </IconTooltipStateWrapper>

  <IconTooltipStateWrapper
    state={layoutType === LayoutType.GROUPED}
    onclick={toggleLayoutType}
    activeTooltip={m["cytoscape.controls.orderByPrerequisites"]()}
    inactiveTooltip={m["cytoscape.controls.groupByDepartment"]()}
  >
    {#snippet active()}
      <Group class="h-5 w-5" />
    {/snippet}
    {#snippet inactive()}
      <Ungroup class="h-5 w-5" />
    {/snippet}
  </IconTooltipStateWrapper>

  <IconTootipWrapper tooltip={m["cytoscape.controls.zoomIn"]()} onclick={zoomIn}>
    <LucidePlus class="h-5 w-5" />
  </IconTootipWrapper>

  <IconTootipWrapper tooltip={m["cytoscape.controls.zoomOut"]()} onclick={zoomOut}>
    <LucideMinus class="h-5 w-5" />
  </IconTootipWrapper>

  <IconTootipWrapper tooltip={m["cytoscape.controls.fullscreen"]()} onclick={toggleFullscreen}>
    <LucideFullscreen class="h-5 w-5" />
  </IconTootipWrapper>
</div>
