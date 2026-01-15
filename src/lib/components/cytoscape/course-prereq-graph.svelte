<script lang="ts">
  import type { Core } from "cytoscape";
  import type { StyleEntry } from "./graph-styles.ts";
  import type { ASTNode } from "$lib/types/course.ts";
  import CytoscapeCore from "./cytoscape-core.svelte";
  import CourseDrawer from "./course-drawer.svelte";
  import { astToElements } from "./cytoscape-init.ts";
  import { fetchCourse } from "./graph-data.ts";
  import { isDesktop } from "$lib/mediaStore.ts";

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

  // Base elements from AST
  const elements = $derived(astToElements(ast, targetCourseId));

  // Track the cytoscape instance to register/unregister handlers
  let registeredCy: Core | undefined = $state();

  /**
   * Add expand nodes positioned to the left of leaf prereq nodes
   */
  function addExpandNodesToGraph(cy: Core) {
    // Remove any existing expand nodes first
    cy.remove(cy.nodes('[type="expand"]'));

    // Find leaf prereq nodes (nodes with no incoming edges, excluding target)
    const leafNodes = cy.nodes('[type="prereq"]').filter((node) => {
      return node.incomers('edge').length === 0;
    });

    const EXPAND_OFFSET = 40; // pixels to the left of the node

    leafNodes.forEach((node) => {
      const courseId = node.id();
      const expandNodeId = `expand-${courseId}`;
      const expandEdgeId = `expand-edge-${courseId}`;
      const pos = node.position();

      // Add expand node positioned to the left
      cy.add([
        {
          data: {
            id: expandNodeId,
            label: "+",
            type: "expand",
            targetCourseId: courseId,
          },
          position: {
            x: pos.x - EXPAND_OFFSET,
            y: pos.y,
          },
        },
        {
          data: {
            id: expandEdgeId,
            source: expandNodeId,
            target: courseId,
            type: "expand-edge",
          },
        },
      ]);
    });
  }

  // Expand node hover handlers
  const expandNodeMouseoverHandler = (event: any) => {
    const targetNode = event.target;
    if (targetNode?.data("type") === "expand") {
      targetNode.addClass("highlighted-nodes");
    }
  };

  const expandNodeMouseoutHandler = (event: any) => {
    const targetNode = event.target;
    if (targetNode?.data("type") === "expand") {
      targetNode.removeClass("highlighted-nodes");
    }
  };

  // Set up expand nodes when cytoscape instance is available
  $effect(() => {
    const cy = cytoscapeCoreRef?.getCyInstance?.();

    // Cleanup previous registration if cy changed
    if (registeredCy && registeredCy !== cy) {
      registeredCy.off("layoutstop");
      registeredCy.off("mouseover", 'node[type="expand"]', expandNodeMouseoverHandler);
      registeredCy.off("mouseout", 'node[type="expand"]', expandNodeMouseoutHandler);
      registeredCy = undefined;
    }

    // Register handler on new cy instance
    if (cy && cy !== registeredCy) {
      // Add expand nodes after initial layout completes
      cy.one("layoutstop", () => {
        addExpandNodesToGraph(cy);
      });

      // Register expand node hover handlers
      cy.on("mouseover", 'node[type="expand"]', expandNodeMouseoverHandler);
      cy.on("mouseout", 'node[type="expand"]', expandNodeMouseoutHandler);

      registeredCy = cy;
    }
  });
</script>

<div class="relative h-full w-full">
  <CytoscapeCore
    elementDefinitions={elements}
    {styleEntries}
    graphType="course"
    bind:this={cytoscapeCoreRef}
  />
</div>
<CourseDrawer
  allowFocusing={false}
  {cytoscapeCoreRef}
  bind:this={courseDrawerRef}
/>
