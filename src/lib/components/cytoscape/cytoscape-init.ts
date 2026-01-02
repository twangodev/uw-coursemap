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
import { CourseUtils, type Course } from "$lib/types/course.ts";

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
  rootCourse: Course,
  takenCourses: string[],
): ElementDefinition[] {
  // Create a temporary headless Cytoscape instance for graph traversal
  const tempCy = cytoscape({
    headless: true,
    elements: elementDefinitions,
  });

  const rootNodeId = CourseUtils.courseReferenceToString(
    rootCourse.course_reference,
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
