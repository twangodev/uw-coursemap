<script lang="ts">
  import type { Core } from "cytoscape";
  import type { StyleEntry } from "./graph-styles.ts";
  import type { ASTNode } from "$lib/types/course.ts";
  import CytoscapeCore from "./cytoscape-core.svelte";
  import CourseDrawer from "./course-drawer.svelte";
  import SideControls from "./side-controls.svelte";
  import { fetchCourse } from "./graph-data.ts";
  import { isDesktop } from "$lib/mediaStore.ts";
  import { createExpandState } from "./expand-state.svelte.ts";

  interface Props {
    /** The prerequisite AST to render */
    ast: ASTNode;
    /** The ID of the target course (e.g., "COMPSCI 240") */
    targetCourseId: string;
    /** Style entries for the graph */
    styleEntries: StyleEntry[];
  }

  let { ast, targetCourseId, styleEntries }: Props = $props();

  // Component refs
  let cytoscapeCoreRef: CytoscapeCore | undefined = $state();
  let courseDrawerRef: CourseDrawer;
  let sideControlsRef: SideControls;

  // Expand state manager - initialized with AST immediately
  const expandState = createExpandState(ast, targetCourseId);

  // Side control handlers
  function handleZoomIn(event: { delta: number }) {
    cytoscapeCoreRef?.zoom(event.delta);
  }

  function handleZoomOut(event: { delta: number }) {
    cytoscapeCoreRef?.zoom(event.delta);
  }

  function handleDraggableChange() {
    cytoscapeCoreRef?.setElementsAreDraggable(sideControlsRef?.getElementsAreDraggable() ?? false);
  }

  // Register course click callback after cytoscape is ready
  $effect(() => {
    if (cytoscapeCoreRef) {
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

  // Track the cytoscape instance to register/unregister handlers
  let registeredCy: Core | undefined = $state();

  // Expand node hover handlers
  const expandNodeMouseoverHandler = (event: any) => {
    const targetNode = event.target;
    if (targetNode?.data("type") === "expand" && !targetNode?.hasClass("expand-faded")) {
      targetNode.addClass("highlighted-nodes");
    }
  };

  const expandNodeMouseoutHandler = (event: any) => {
    const targetNode = event.target;
    if (targetNode?.data("type") === "expand" && !targetNode?.hasClass("expand-faded")) {
      targetNode.removeClass("highlighted-nodes");
    }
  };

  // Expand node click handler
  const expandNodeClickHandler = async (event: any) => {
    const targetNode = event.target;
    if (targetNode?.data("type") !== "expand" || targetNode?.hasClass("expand-faded")) return;

    const courseId = targetNode.data("targetCourseId");
    const isExpanded = expandState.isExpanded(courseId);

    if (!isExpanded) {
      await expandState.expandCourse(courseId);
    } else {
      await expandState.collapseCourse(courseId);
    }
  };

  // Initialize expand state and set up handlers when cytoscape is ready
  $effect(() => {
    const cy = cytoscapeCoreRef?.getCyInstance?.();

    // Cleanup previous registration if cy changed
    if (registeredCy && registeredCy !== cy) {
      registeredCy.off("mouseover", 'node[type="expand"]', expandNodeMouseoverHandler);
      registeredCy.off("mouseout", 'node[type="expand"]', expandNodeMouseoutHandler);
      registeredCy.off("tap", 'node[type="expand"]', expandNodeClickHandler);
      registeredCy = undefined;
    }

    // Register handler on new cy instance
    if (cy && cy !== registeredCy) {
      // Set cytoscape instance in expand state (automatically adds expand nodes after layout)
      expandState.setCytoscape(cy);

      // Register expand node event handlers
      cy.on("mouseover", 'node[type="expand"]', expandNodeMouseoverHandler);
      cy.on("mouseout", 'node[type="expand"]', expandNodeMouseoutHandler);
      cy.on("tap", 'node[type="expand"]', expandNodeClickHandler);

      registeredCy = cy;
    }
  });
</script>

<div id="cy-container" class="relative h-full w-full">
  <CytoscapeCore
    elementDefinitions={expandState.elements}
    {styleEntries}
    graphType="course"
    bind:this={cytoscapeCoreRef}
  />
  <SideControls
    bind:this={sideControlsRef}
    onzoomin={handleZoomIn}
    onzoomout={handleZoomOut}
    ondraggablechange={handleDraggableChange}
  />
</div>
<CourseDrawer
  allowFocusing={false}
  {cytoscapeCoreRef}
  bind:this={courseDrawerRef}
/>
