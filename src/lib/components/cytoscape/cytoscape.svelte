<script lang="ts">
  import type { ElementDefinition } from "cytoscape";
  import { fetchCourse } from "./graph-data.ts";
  import type { StyleEntry, GraphType } from "./graph-styles.ts";
  import SideControls from "./side-controls.svelte";
  import CourseDrawer from "./course-drawer.svelte";
  import CytoscapeCore from "./cytoscape-core.svelte";
  import Legend from "./legend.svelte";
  import HelpControl from "./help-control.svelte";
  import { isDesktop } from "$lib/mediaStore.ts";
  import { LayoutType } from "./graph-layout.ts";
  import { computeLayout } from "./cytoscape-init.ts";

  interface Props {
    elementDefinitions: ElementDefinition[];
    styleEntries: StyleEntry[];
    allowFocusing?: boolean;
    graphType?: GraphType;
  }

  let {
    elementDefinitions,
    styleEntries,
    allowFocusing = true,
    graphType = "department",
  }: Props = $props();

  // Component refs
  let cytoscapeCoreRef: CytoscapeCore | undefined = $state();
  let courseDrawerRef: CourseDrawer;
  let sideControlsRef: SideControls;

  // Legend state
  let hiddenSubject: string | null = $state(null);

  // Wire legend hiding to cytoscape core
  $effect(() => {
    cytoscapeCoreRef?.setHiddenSubject(hiddenSubject);
  });

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

  function handleZoom(event: { delta: number }) {
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
    {graphType}
    bind:this={cytoscapeCoreRef}
  />

  <Legend {styleEntries} bind:hiddenSubject />
  <SideControls
    bind:this={sideControlsRef}
    onzoomin={handleZoom}
    onzoomout={handleZoom}
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
