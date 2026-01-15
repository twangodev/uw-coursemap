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
  /** Element IDs that this expansion "owns" (for tracking what to clean up) */
  ownedElementIds: string[];
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

  /** Tracks expanded courses and their owned elements */
  const expandedCourses = new Map<string, ExpandedCourseInfo>();

  /** Reference count for each element ID - how many expansions need this element */
  const elementRefCount = new Map<string, number>();

  /**
   * Initialize reference counts for initial elements
   */
  function initRefCounts(): void {
    for (const el of coreElements) {
      const id = el.data.id as string;
      if (id) {
        elementRefCount.set(id, 1);
      }
    }
  }

  // Initialize ref counts for initial elements
  initRefCounts();

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
   * Get valid elements for layout (filter out edges pointing to non-existent nodes)
   */
  function getValidElementsForLayout(): ElementDefinition[] {
    const nodeIds = new Set<string>();

    // Collect all node IDs
    for (const el of coreElements) {
      if (!el.data.source && !el.data.target) {
        nodeIds.add(el.data.id as string);
      }
    }

    // Filter: keep all nodes, and only edges where both source and target exist
    return coreElements.filter((el) => {
      if (!el.data.source && !el.data.target) {
        return true; // Keep all nodes
      }
      // It's an edge - check both endpoints exist
      return nodeIds.has(el.data.source as string) && nodeIds.has(el.data.target as string);
    });
  }

  /**
   * Run layout on core elements and add expand nodes after
   */
  async function runLayout(): Promise<void> {
    if (!cyInstance) return;

    // Remove expand nodes before layout (they'll be re-added after)
    removeExpandNodes();

    const validElements = getValidElementsForLayout();
    const layoutOptions = await generateTreeLayout(true, validElements, true);

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
        const ownedElementIds: string[] = [];
        const elementsToAdd: ElementDefinition[] = [];

        // Process each element - skip duplicate nodes but always add edges
        for (const el of newElements) {
          const id = el.data.id as string;
          if (id === courseId) continue;

          const isEdge = el.data.source && el.data.target;

          if (isEdge) {
            // Edges are always unique per expansion - always add them
            ownedElementIds.push(id);
            elementsToAdd.push(el);
            elementRefCount.set(id, 1);
          } else {
            // Node - check for duplicates
            ownedElementIds.push(id);

            const currentRefCount = elementRefCount.get(id) || 0;
            if (currentRefCount === 0) {
              // New node - add to graph
              elementsToAdd.push(el);
              elementRefCount.set(id, 1);
            } else {
              // Existing node - just increment ref count
              elementRefCount.set(id, currentRefCount + 1);
            }
          }
        }

        // Add new elements to core elements and Cytoscape
        if (elementsToAdd.length > 0) {
          coreElements = [...coreElements, ...elementsToAdd];
          cyInstance.add(elementsToAdd);
        }

        // Track expansion
        expandedCourses.set(courseId, { ownedElementIds });

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
            // Check if source is one of the owned elements
            const sourceId = edge.data("source");
            if (ownedElementIds.includes(sourceId)) {
              edge.move({ target: expandNodeId });
            }
          }
        });
      } catch (error) {
        console.error(`Failed to expand ${courseId}:`, error);
      }
    },

    /**
     * Collapse a course: remove prerequisite subtree and all nested expansions, run layout
     */
    async collapseCourse(courseId: string): Promise<void> {
      if (!cyInstance) return;

      const expandInfo = expandedCourses.get(courseId);
      if (!expandInfo) return;

      // Recursively find all nested expanded courses
      function findAllNestedExpanded(rootCourseId: string): string[] {
        const info = expandedCourses.get(rootCourseId);
        if (!info) return [];

        const nested: string[] = [];
        const { ownedElementIds } = info;

        // Find direct children that are expanded
        expandedCourses.forEach((_, nestedCourseId) => {
          if (nestedCourseId !== rootCourseId && ownedElementIds.includes(nestedCourseId)) {
            nested.push(nestedCourseId);
            // Recursively find their nested expansions
            nested.push(...findAllNestedExpanded(nestedCourseId));
          }
        });

        return nested;
      }

      /**
       * Decrement ref counts and remove elements that reach zero
       */
      function releaseElements(elementIds: string[]): void {
        const elementsToRemove: string[] = [];

        for (const id of elementIds) {
          const currentRefCount = elementRefCount.get(id) || 0;
          if (currentRefCount <= 1) {
            // Last reference - remove element
            elementRefCount.delete(id);
            elementsToRemove.push(id);
          } else {
            // Other expansions still need this element
            elementRefCount.set(id, currentRefCount - 1);
          }
        }

        // Remove elements from Cytoscape
        for (const id of elementsToRemove) {
          cyInstance!.$id(id).remove();
        }

        // Remove from coreElements
        if (elementsToRemove.length > 0) {
          const removeSet = new Set(elementsToRemove);
          coreElements = coreElements.filter((el) => {
            const id = el.data.id as string;
            return !removeSet.has(id);
          });
        }
      }

      // Get all nested expanded courses (deepest first for proper removal order)
      const allNested = findAllNestedExpanded(courseId).reverse();

      // Remove all nested expansions
      for (const nestedCourseId of allNested) {
        const nestedInfo = expandedCourses.get(nestedCourseId);
        if (nestedInfo) {
          releaseElements(nestedInfo.ownedElementIds);
          expandedCourses.delete(nestedCourseId);
        }
      }

      // Now release the elements for this course
      releaseElements(expandInfo.ownedElementIds);
      expandedCourses.delete(courseId);

      await runLayout();
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
      elementRefCount.clear();
      cyInstance = null;
    },
  };
}

export type ExpandState = ReturnType<typeof createExpandState>;
