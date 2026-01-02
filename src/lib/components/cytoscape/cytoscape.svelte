<script lang="ts">
  import type { ElementDefinition } from "cytoscape";
  import { fetchCourse } from "./graph-data.ts";
  import type { StyleEntry } from "./graph-styles.ts";
  import SideControls from "./side-controls.svelte";
  import CourseDrawer from "./course-drawer.svelte";
  import CytoscapeCore from "./cytoscape-core.svelte";
  import Legend from "./legend.svelte";
  import HelpControl from "./help-control.svelte";
  import { onMount } from "svelte";
  import { isDesktop } from "$lib/mediaStore.ts";
  import { LayoutType } from "./graph-layout.ts";
  import { computeLayout } from "./cytoscape-init.ts";

  interface Props {
    elementDefinitions: ElementDefinition[];
    styleEntries: StyleEntry[];
    allowFocusing?: boolean;
  }

  let {
    elementDefinitions,
    styleEntries,
    allowFocusing = true,
  }: Props = $props();

  // Component refs
  let cytoscapeCoreRef: CytoscapeCore | undefined = $state();
  let courseDrawerRef: CourseDrawer;
  let sideControlsRef: SideControls;

  // Initialize
  $effect(() => {
    if (cytoscapeCoreRef) {
      // Register course click callback after cytoscape is ready
      cytoscapeCoreRef.onCourseClick((courseId) => {
        if ($isDesktop) {
          fetchCourse(courseId).then((course) => {
            courseDrawerRef.setSelectedCourse(course);
            courseDrawerRef.openDrawer();
          }).catch((error) => {
            console.error("Failed to fetch course:", error);
          });
        }
      });
    }
  });

  // Event handlers from SideControls
  function handleZoomIn(event: { delta: number }) {
    cytoscapeCoreRef?.zoom(event.delta);
  }

  function handleZoomOut(event: { delta: number }) {
    cytoscapeCoreRef?.zoom(event.delta);
  }

  async function handleLayoutChange() {
    const layout = await computeLayout({
      layoutType: sideControlsRef?.getLayoutType() ?? LayoutType.LAYERED,
      elementDefinitions,
      animate: true,
      showCodeLabels: sideControlsRef?.getShowCodeLabels() ?? true,
    });

    cytoscapeCoreRef?.runLayout(layout);
  }

  function handleDraggableChange() {
    cytoscapeCoreRef?.setElementsAreDraggable(sideControlsRef?.getElementsAreDraggable() ?? false);
  }

  function handleLabelChange() {
    cytoscapeCoreRef?.setShowCodeLabels(sideControlsRef?.getShowCodeLabels() ?? true);
  }
</script>

<div id="cy-container" class="relative h-full w-full">
  <CytoscapeCore
    {elementDefinitions}
    {styleEntries}
    bind:this={cytoscapeCoreRef}
  />

  <Legend {styleEntries} />
  <SideControls
    bind:this={sideControlsRef}
    onzoomin={handleZoomIn}
    onzoomout={handleZoomOut}
    onlayoutchange={handleLayoutChange}
    ondraggablechange={handleDraggableChange}
    onlabelchange={handleLabelChange}
  />
  <HelpControl />
</div>
<CourseDrawer
  {allowFocusing}
  {cytoscapeCoreRef}
  bind:this={courseDrawerRef}
/>
