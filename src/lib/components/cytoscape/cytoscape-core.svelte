<script lang="ts">
  import { onMount } from "svelte";
  import {
    type Core,
    type ElementDefinition,
    type LayoutOptions,
  } from "cytoscape";
  import {
    initializeCytoscape,
    computeLayout,
  } from "./cytoscape-init.ts";
  import { LayoutType } from "./graph-layout.ts";
  import {
    getStyles,
    getCourseGraphStyles,
    type StyleEntry,
    type GraphType,
  } from "./graph-styles.ts";
  import { setupCytoscapeHandlers } from "./cytoscape-handlers.svelte.ts";
  import { clearPath, highlightPath } from "./paths.ts";
  import { cn } from "$lib/utils.ts";
  import { mode } from "mode-watcher";

  interface Props {
    elementDefinitions: ElementDefinition[];
    styleEntries: StyleEntry[];
    graphType?: GraphType;
  }

  let {
    elementDefinitions,
    styleEntries,
    graphType = "department",
  }: Props = $props();

  let cy: Core | undefined = $state();
  let handler: ReturnType<typeof setupCytoscapeHandlers> | undefined;

  onMount(() => {
    const container = document.getElementById("cy");
    if (!container) {
      console.error("Cytoscape container not found");
      return;
    }

    // Create Cytoscape instance with appropriate styles based on graph type
    const initialStyles =
      graphType === "course"
        ? getCourseGraphStyles()
        : getStyles(styleEntries, mode.current, true);

    cy = initializeCytoscape({
      container,
      elementDefinitions,
      style: initialStyles,
    });

    // Setup handlers with graph type
    handler = setupCytoscapeHandlers(cy, graphType);

    // Run initial layout (async, but we don't need to await)
    // Use tree layout for course graphs, layered for department
    const layoutType =
      graphType === "course" ? LayoutType.TREE : LayoutType.LAYERED;

    computeLayout({
      layoutType,
      elementDefinitions,
      animate: false,
      showCodeLabels: true,
    }).then((layout) => {
      const layoutInstance = cy?.layout(layout);
      layoutInstance?.one("layoutstop", () => {
        // Center the graph after layout completes
        cy?.fit(undefined, 30);
        cy?.center();
      });
      layoutInstance?.run();
    });

    return () => {
      handler?.cleanup();
      cy?.destroy();
    };
  });

  
  // PUBLIC API - Methods parent can call via ref

  /**
   * Register callback for course click events (opens drawer, etc.)
   */
  export function onCourseClick(callback: (courseId: string) => void) {
    handler?.onCourseClick(callback);
  }

  /**
   * Zoom in or out by delta amount
   */
  export function zoom(delta: number) {
    if (!cy) return;
    cy.zoom(cy.zoom() + delta);
  }

  /**
   * Run a layout on the graph
   */
  export function runLayout(layoutOptions: LayoutOptions) {
    cy?.layout(layoutOptions).run();
  }

  /**
   * Set whether to show course codes or titles
   */
  export function setShowCodeLabels(show: boolean) {
    handler?.setShowCodeLabels(show);
  }

  /**
   * Set the hidden subject
   */
  export function setHiddenSubject(subject: string | null) {
    handler?.setHiddenSubject(subject);
  }

  /**
   * Set whether elements are draggable
   */
  export function setElementsAreDraggable(draggable: boolean) {
    handler?.setElementsAreDraggable(draggable);
  }

  /**
   * Focus on a course by ID - animates to center and highlights path
   */
  export function focusOnCourse(courseId: string) {
    if (!cy) return;

    const node = cy.$id(courseId);
    if (!node || node.empty()) return;

    cy.animate({
      zoom: 2,
      center: { eles: node },
      duration: 1000,
      easing: "ease-in-out",
      queue: true,
    });

    clearPath(cy, () => handler?.destroyTip());
    highlightPath(cy, node);
  }
</script>

<div id="cy" class={cn("h-full w-full transition-opacity")}></div>
