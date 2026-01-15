/**
 * State management for expandable course prerequisite graph.
 * Handles expansion, collapsing, fetching prerequisites, and layout computation.
 */

import type { Core, ElementDefinition } from "cytoscape";
import type { ASTNode } from "$lib/types/course.ts";
import { astToElements } from "./cytoscape-init.ts";
import { fetchCourse } from "./graph-data.ts";
import { generateTreeLayout } from "./graph-layout.ts";

const EXPAND_OFFSET = 40;

/** Info about an expanded course */
interface ExpandedCourseInfo {
  addedElementIds: string[];
}

/**
 * Creates expand state management for the course graph.
 * @param initialAst - The initial prerequisite AST
 * @param initialTargetCourseId - The initial target course ID
 */
export function createExpandState(initialAst: ASTNode, initialTargetCourseId: string) {
  /** Core elements - reactive state that course-prereq-graph reads */
  let coreElements = $state<ElementDefinition[]>(astToElements(initialAst, initialTargetCourseId));

  /** Cytoscape instance */
  let cyInstance: Core | null = null;

  /** Tracks expanded courses and their added elements */
  const expandedCourses = new Map<string, ExpandedCourseInfo>();

  /**
   * Remove all expand nodes and their edges from cytoscape
   */
  function removeExpandNodes(): void {
    if (!cyInstance) return;
    cyInstance.remove('node[type="expand"]');
    cyInstance.remove('edge[type="expand-edge"]');
  }

  /**
   * Add expand nodes to leaf prereq nodes and expanded courses after layout
   */
  function addExpandNodes(): void {
    if (!cyInstance) return;

    // Find leaf prereq nodes (no incoming edges from non-expand edges)
    const leafNodes = cyInstance.nodes('[type="prereq"]').filter((node) => {
      const nonExpandIncomers = node.incomers("edge").filter((edge) => {
        return edge.data("type") !== "expand-edge";
      });
      return nonExpandIncomers.length === 0;
    });

    // Collect all nodes that need expand buttons: leaves + expanded courses
    const nodesNeedingExpand = new Set<string>();

    leafNodes.forEach((node) => {
      nodesNeedingExpand.add(node.id());
    });

    // Also add expand nodes for already expanded courses (for collapse)
    expandedCourses.forEach((_, courseId) => {
      nodesNeedingExpand.add(courseId);
    });

    nodesNeedingExpand.forEach((courseId) => {
      const node = cyInstance!.$id(courseId);
      if (node.length === 0) return;

      const expandNodeId = `expand-${courseId}`;

      // Skip if already exists
      if (cyInstance!.$id(expandNodeId).length > 0) return;

      const pos = node.position();
      const isExpanded = expandedCourses.has(courseId);

      cyInstance!.add([
        {
          data: {
            id: expandNodeId,
            label: isExpanded ? "-" : "+",
            type: "expand",
            targetCourseId: courseId,
          },
          position: { x: pos.x - EXPAND_OFFSET, y: pos.y },
        },
        {
          data: {
            id: `expand-edge-${courseId}`,
            source: expandNodeId,
            target: courseId,
            type: "expand-edge",
          },
        },
      ]);
    });
  }

  /**
   * Run layout on core elements and add expand nodes after
   */
  async function runLayout(): Promise<void> {
    if (!cyInstance) return;

    // Remove expand nodes before layout (they'll be re-added after)
    removeExpandNodes();

    const layoutOptions = await generateTreeLayout(true, coreElements, true);

    cyInstance.layout(layoutOptions).run();

    cyInstance.one("layoutstop", () => {
      addExpandNodes();
    });
  }

  return {
    /**
     * Get core elements (reactive)
     */
    get elements(): ElementDefinition[] {
      return coreElements;
    },

    /**
     * Set the cytoscape instance (call after cy is ready)
     * Automatically adds expand nodes after initial layout completes
     */
    setCytoscape(cy: Core): void {
      cyInstance = cy;

      // Add expand nodes after initial layout completes
      cy.one("layoutstop", () => {
        addExpandNodes();
      });
    },

    /**
     * Expand a course: fetch prerequisites, add to graph, run layout
     */
    async expandCourse(courseId: string): Promise<void> {
      if (!cyInstance) return;
      if (expandedCourses.has(courseId)) return;

      try {
        const course = await fetchCourse(courseId);
        const ast = course.prerequisites?.abstract_syntax_tree;

        if (!ast) {
          console.log(`No prerequisites for ${courseId}`);
          return;
        }

        // Convert AST to elements (edges point to courseId)
        const newElements = astToElements(ast, courseId);
        const addedElementIds: string[] = [];

        // Filter out the course itself and track added IDs
        for (const el of newElements) {
          const id = el.data.id as string;
          if (id === courseId) continue;
          addedElementIds.push(id);
        }

        // Add to core elements (edges still point to courseId for ELK)
        const elementsToAdd = newElements.filter((el) => el.data.id !== courseId);
        coreElements = [...coreElements, ...elementsToAdd];

        // Add elements to Cytoscape instance
        cyInstance.add(elementsToAdd);

        // Track expansion
        expandedCourses.set(courseId, { addedElementIds });

        // Update expand node label to "-"
        const expandNodeId = `expand-${courseId}`;
        const expandNode = cyInstance.$id(expandNodeId);
        if (expandNode.length > 0) {
          expandNode.data("label", "-");
        }

        await runLayout();

        // After layout, redirect edges in cytoscape to point to expand node
        cyInstance.edges().forEach((edge) => {
          if (edge.data("target") === courseId) {
            // Check if source is one of the newly added elements
            const sourceId = edge.data("source");
            if (addedElementIds.includes(sourceId)) {
              edge.move({ target: expandNodeId });
            }
          }
        });
      } catch (error) {
        console.error(`Failed to expand ${courseId}:`, error);
      }
    },

    /**
     * Collapse a course: remove prerequisite subtree, run layout
     */
    async collapseCourse(courseId: string): Promise<void> {
      // TODO: Remove elements added during expansion, run layout
    },

    /**
     * Check if a course is expanded
     */
    isExpanded(courseId: string): boolean {
      return expandedCourses.has(courseId);
    },

    /**
     * Clear all state
     */
    clear(): void {
      coreElements = [];
      expandedCourses.clear();
      cyInstance = null;
    },
  };
}

export type ExpandState = ReturnType<typeof createExpandState>;
