import cytoscape, { type ElementDefinition, type StylesheetStyle } from "cytoscape";
import cytoscapeFcose from "cytoscape-fcose";
import cytoscapePopper from "cytoscape-popper";
import tippy from "tippy.js";
import {
  generateFcoseLayout,
  generateLayeredLayout,
  LayoutType,
} from "./graph-layout.ts";
import { getPredecessorsNotTaken } from "./paths.ts";
import { CourseUtils, type CourseReference, type ASTNode, type ASTOperatorNode } from "$lib/types/course.ts";

/**
 * Options for computing layout
 */
export interface ComputeLayoutOptions {
  layoutType: LayoutType;
  elementDefinitions: ElementDefinition[];
  animate: boolean;
  showCodeLabels: boolean;
}

/**
 * Factory function for creating tippy tooltips with Cytoscape Popper
 */
function tippyFactory(ref: any, content: any) {
  // Since tippy constructor requires DOM element/elements, create a placeholder
  const dummyDomEle = document.createElement("div");

  return tippy(dummyDomEle, {
    getReferenceClientRect: ref.getBoundingClientRect,
    trigger: "manual", // mandatory
    content: content,
    arrow: true,
    placement: "bottom",
    hideOnClick: true,
    sticky: "reference",
    interactive: true,
    appendTo: document.body,
  });
}

/**
 * Registers all required Cytoscape plugins
 * Called internally by initializeCytoscape
 */
function registerPlugins(): void {
  cytoscape.use(cytoscapeFcose);
  cytoscape.use(cytoscapePopper(tippyFactory));
}

// Track if plugins have been registered
let pluginsRegistered = false;

/**
 * Options for initializing a Cytoscape instance
 */
export interface InitializeCytoscapeOptions {
  container: HTMLElement;
  elementDefinitions: ElementDefinition[];
  style?: StylesheetStyle[];
  minZoom?: number;
  maxZoom?: number;
  motionBlur?: boolean;
}

/**
 * Creates and initializes a minimal Cytoscape instance
 * Automatically registers plugins on first call
 * Style and layout can be applied later using cy.style() and cy.layout()
 *
 * @param options - Initialization options
 * @returns Initialized Cytoscape core instance
 */
export function initializeCytoscape(
  options: InitializeCytoscapeOptions,
): cytoscape.Core {
  // Register plugins once
  if (!pluginsRegistered) {
    registerPlugins();
    pluginsRegistered = true;
  }

  const {
    container,
    elementDefinitions,
    style,
    minZoom = 0.01,
    maxZoom = 2,
    motionBlur = true,
  } = options;

  return cytoscape({
    container,
    elements: elementDefinitions,
    style,
    minZoom,
    maxZoom,
    motionBlur,
  });
}

/**
 * Computes the appropriate layout based on layout type and options
 *
 * @param options - Layout computation options
 * @returns Layout configuration object
 */
export async function computeLayout(
  options: ComputeLayoutOptions,
): Promise<cytoscape.LayoutOptions> {
  const { layoutType, elementDefinitions, animate, showCodeLabels } = options;

  const layout =
    layoutType === LayoutType.GROUPED
      ? generateFcoseLayout(animate)
      : await generateLayeredLayout(animate, elementDefinitions, showCodeLabels);

  return layout;
}

/**
 * Filters elements to show only prerequisites of a root course
 * Uses DFS traversal to find all prerequisite courses leading to the root
 *
 * @param elementDefinitions - All graph elements
 * @param rootCourse - The course to trace prerequisites from
 * @param takenCourses - List of already taken course IDs (stops traversal)
 * @returns Filtered element definitions containing only prerequisite paths
 */
export function filterElementsByRootCourse(
  elementDefinitions: ElementDefinition[],
  rootCourse: CourseReference,
  takenCourses: string[],
): ElementDefinition[] {
  // Create a temporary headless Cytoscape instance for graph traversal
  const tempCy = cytoscape({
    headless: true,
    elements: elementDefinitions,
  });

  const rootNodeId = CourseUtils.courseReferenceToString(
    rootCourse
  );
  const rootNode = tempCy.$id(rootNodeId)[0];

  if (!rootNode) {
    tempCy.destroy();
    return elementDefinitions;
  }

  // Get all predecessors that are not in takenCourses
  const keepData = getPredecessorsNotTaken(rootNode, takenCourses);

  // Remove nodes that are not in the prerequisite path
  const nodesToRemove = tempCy
    .nodes()
    .filter((node: cytoscape.NodeSingular) => {
      return (
        !keepData.includes(node.id()) && node.data("type") !== "compound"
      );
    });

  tempCy.remove(nodesToRemove);

  // Get the remaining elements as JSON
  const filteredElements = tempCy.elements().jsons() as ElementDefinition[];
  tempCy.destroy();

  return filteredElements;
}

/**
 * Converts a prerequisite AST to Cytoscape element definitions
 * - Course references become nodes
 * - OR operators become "one of" nodes with children branching off
 * - AND operators connect all children directly to the parent
 * - String nodes (like "graduate standing") are ignored
 *
 * @param ast - The abstract syntax tree node to convert
 * @param targetCourseId - The ID of the course these are prerequisites for
 * @returns Array of Cytoscape element definitions (nodes and edges)
 */
export function astToElements(
  ast: ASTNode,
  targetCourseId: string
): ElementDefinition[] {
  const nodes: ElementDefinition[] = [];
  const edges: ElementDefinition[] = [];
  let oneOfCounter = 0;
  let andCounter = 0;

  function isCourseReference(node: ASTNode): node is CourseReference {
    return (
      typeof node === "object" &&
      "course_number" in node &&
      "subjects" in node
    );
  }

  function isOperatorNode(node: ASTNode): node is ASTOperatorNode {
    return (
      typeof node === "object" &&
      "operator" in node &&
      "children" in node
    );
  }

  /**
   * Recursively processes an AST node
   * @returns The node ID that should connect to the parent, or null if none
   */
  function processNode(node: ASTNode, parentId: string): string | null {
    // Skip string nodes (e.g., "graduate standing")
    if (typeof node === "string") {
      return null;
    }

    // Course reference node
    if (isCourseReference(node)) {
      const id = CourseUtils.courseReferenceToString(node);
      // Use only first subject, truncated to 4 chars (e.g., "COMP 240" instead of "COMPSCI/MATH 240")
      const firstSubject = [...node.subjects].sort()[0].slice(0, 4);
      const label = `${firstSubject} ${node.course_number}`;

      // Only add node if not already present
      if (!nodes.some((n) => n.data.id === id)) {
        nodes.push({
          data: { id, label, type: "prereq" },
        });
      }

      return id;
    }

    // Operator node
    if (isOperatorNode(node)) {
      if (node.operator === "OR") {
        // First, collect all valid child IDs
        const childIds: string[] = [];
        for (const child of node.children) {
          const childId = processNode(child, parentId);
          if (childId) {
            childIds.push(childId);
          }
        }

        // If only one valid child, just return it directly (no "one of" needed)
        if (childIds.length === 1) {
          return childIds[0];
        }

        // If multiple valid children, create a "one of" node
        if (childIds.length > 1) {
          const oneOfId = `one-of-${oneOfCounter++}`;
          nodes.push({
            data: { id: oneOfId, label: "one of", type: "operator" },
          });

          // Connect all children to the "one of" node
          for (const childId of childIds) {
            edges.push({
              data: { source: childId, target: oneOfId },
            });
          }

          return oneOfId;
        }

        // No valid children
        return null;
      } else {
        // AND operator - create an "and" node like OR creates "one of"
        const childIds: string[] = [];

        for (const child of node.children) {
          const childId = processNode(child, parentId);
          if (childId) {
            childIds.push(childId);
          }
        }

        // If only one valid child, just return it directly (no "and" needed)
        if (childIds.length === 1) {
          return childIds[0];
        }

        // If multiple valid children, create an "and" node
        if (childIds.length > 1) {
          const andId = `and-${andCounter++}`;
          nodes.push({
            data: { id: andId, label: "and", type: "operator" },
          });

          // Connect all children to the "and" node
          for (const childId of childIds) {
            edges.push({
              data: { source: childId, target: andId },
            });
          }

          return andId;
        }

        // No valid children
        return null;
      }
    }

    return null;
  }

  // Add the target course node
  // Parse targetCourseId to get short label (e.g., "COMPSCI/MATH 240" -> "COMP 240")
  const parts = targetCourseId.split(" ");
  const subjects = parts[0].split("/").sort();
  const courseNumber = parts[1];
  const targetLabel = `${subjects[0].slice(0, 4)} ${courseNumber}`;

  nodes.push({
    data: { id: targetCourseId, label: targetLabel, type: "target" },
  });

  // Process the AST
  const rootResult = processNode(ast, targetCourseId);

  // If root returned an ID (e.g., single OR node), connect it to target
  if (rootResult) {
    edges.push({
      data: { source: rootResult, target: targetCourseId },
    });
  }

  return [...nodes, ...edges];
}
