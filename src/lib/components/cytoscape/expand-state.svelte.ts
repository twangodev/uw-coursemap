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
   * Add expand nodes to leaf prereq nodes after layout
   */
  function addExpandNodes(): void {
    if (!cyInstance) return;

    // Find leaf prereq nodes (no incoming edges)
    const leafNodes = cyInstance.nodes('[type="prereq"]').filter((node) => {
      return node.incomers("edge").length === 0;
    });

    leafNodes.forEach((node) => {
      const courseId = node.id();
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
