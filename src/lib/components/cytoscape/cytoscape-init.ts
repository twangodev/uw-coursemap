import cytoscape, { type ElementDefinition, type StylesheetStyle } from "cytoscape";
import cytoscapeFcose from "cytoscape-fcose";
import cytoscapePopper from "cytoscape-popper";
import tippy from "tippy.js";
import {
  generateFcoseLayout,
  generateLayeredLayout,
  generateTreeLayout,
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

  switch (layoutType) {
    case LayoutType.GROUPED:
      return generateFcoseLayout(animate);
    case LayoutType.LAYERED:
      return await generateLayeredLayout(animate, elementDefinitions, showCodeLabels);
    case LayoutType.TREE:
      return await generateTreeLayout(animate, elementDefinitions, showCodeLabels);
  }
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
  let edgeCounter = 0;

  /** Generate a unique edge ID based on source, target, and context */
  function createEdgeId(source: string, target: string): string {
    return `edge-${targetCourseId}-${source}-${target}-${edgeCounter++}`;
  }

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
   * Parent context passed to child nodes during processing
   */
  interface ParentContext {
    operatorId: string | null;
    operatorType: "OR" | "AND" | null;
  }

  /**
   * Recursively processes an AST node
   * @param node - The AST node to process
   * @param parentId - The parent node ID (unused but kept for signature)
   * @param parentContext - Info about the parent operator (for tracking OR/AND relationships)
   * @returns The node ID that should connect to the parent, or null if none
   */
  function processNode(
    node: ASTNode,
    parentId: string,
    parentContext: ParentContext = { operatorId: null, operatorType: null }
  ): string | null {
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
          data: {
            id,
            label,
            type: "prereq",
            parentOperatorId: parentContext.operatorId,
            parentOperatorType: parentContext.operatorType,
          },
          classes: "hoverable course",
        });
      }

      return id;
    }

    // Operator node
    if (isOperatorNode(node)) {
      if (node.operator === "OR") {
        // Create the operator node first to get its ID for child context
        const oneOfId = `one-of-${targetCourseId}-${oneOfCounter++}`;

        // Collect all valid child IDs, passing this operator as parent context
        const childIds: string[] = [];
        for (const child of node.children) {
          const childId = processNode(child, parentId, {
            operatorId: oneOfId,
            operatorType: "OR",
          });
          if (childId) {
            childIds.push(childId);
          }
        }

        // If only one valid child, just return it directly (no "one of" needed)
        // But we need to remove the parentOperatorId since the operator won't exist
        if (childIds.length === 1) {
          // Update the child node to remove parent operator reference
          const childNode = nodes.find((n) => n.data.id === childIds[0]);
          if (childNode && childNode.data.parentOperatorId === oneOfId) {
            childNode.data.parentOperatorId = parentContext.operatorId;
            childNode.data.parentOperatorType = parentContext.operatorType;
          }
          oneOfCounter--; // Reclaim the unused ID
          return childIds[0];
        }

        // If multiple valid children, keep the "one of" node
        if (childIds.length > 1) {
          nodes.push({
            data: { id: oneOfId, label: "one of", type: "operator" },
            classes: "hoverable",
          });

          // Connect all children to the "one of" node
          for (const childId of childIds) {
            edges.push({
              data: { id: createEdgeId(childId, oneOfId), source: childId, target: oneOfId },
            });
          }

          return oneOfId;
        }

        // No valid children
        oneOfCounter--; // Reclaim the unused ID
        return null;
      } else {
        // AND operator - create an "all of" node
        const andId = `and-${targetCourseId}-${andCounter++}`;

        // Collect all valid child IDs, passing this operator as parent context
        const childIds: string[] = [];
        for (const child of node.children) {
          const childId = processNode(child, parentId, {
            operatorId: andId,
            operatorType: "AND",
          });
          if (childId) {
            childIds.push(childId);
          }
        }

        // If only one valid child, just return it directly (no "and" needed)
        if (childIds.length === 1) {
          // Update the child node to remove parent operator reference
          const childNode = nodes.find((n) => n.data.id === childIds[0]);
          if (childNode && childNode.data.parentOperatorId === andId) {
            childNode.data.parentOperatorId = parentContext.operatorId;
            childNode.data.parentOperatorType = parentContext.operatorType;
          }
          andCounter--; // Reclaim the unused ID
          return childIds[0];
        }

        // If multiple valid children, keep the "and" node
        if (childIds.length > 1) {
          nodes.push({
            data: { id: andId, label: "all of", type: "operator" },
            classes: "hoverable",
          });

          // Connect all children to the "and" node
          for (const childId of childIds) {
            edges.push({
              data: { id: createEdgeId(childId, andId), source: childId, target: andId },
            });
          }

          return andId;
        }

        // No valid children
        andCounter--; // Reclaim the unused ID
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
    classes: "hoverable course",
  });

  // Process the AST
  const rootResult = processNode(ast, targetCourseId);

  // If root returned an ID (e.g., single OR node), connect it to target
  if (rootResult) {
    edges.push({
      data: { id: createEdgeId(rootResult, targetCourseId), source: rootResult, target: targetCourseId },
    });
  }

  return [...nodes, ...edges];
}
