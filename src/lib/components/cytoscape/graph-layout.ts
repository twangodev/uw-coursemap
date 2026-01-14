import type {
  EdgeDefinition,
  ElementDefinition,
  LayoutOptions,
  NodeDefinition,
} from "cytoscape";
import ELK, { type ElkNode } from "elkjs/lib/elk.bundled.js";
import { getEdgeData, getNodeData } from "./graph-data.ts";
import {
  COURSE_GRAPH_FONT_SIZE,
  COURSE_GRAPH_OPERATOR_FONT_SIZE,
  COURSE_GRAPH_NODE_PADDING_X,
  COURSE_GRAPH_NODE_PADDING_Y,
} from "./graph-styles.ts";

export enum LayoutType {
  GROUPED,
  LAYERED,
  TREE,
}

/**
 * Measures text width using canvas
 */
function measureTextWidth(text: string, fontSize: number): number {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return text.length * fontSize * 0.6; // Fallback estimate

  ctx.font = `${fontSize}px sans-serif`;
  return ctx.measureText(text).width;
}

export async function generateLayeredLayout(
  animate: boolean,
  courseData: ElementDefinition[],
  labelIsCode: boolean,
): Promise<LayoutOptions> {
  const elk = new ELK();
  const newLayout: ElkNode = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.randomSeed": `${Math.floor(Math.random() * 1000)}`,
      "elk.spacing.nodeNode": "20",
      "elk.layered.spacing.nodeNodeBetweenLayers": "50",
    },
    children: getNodeData(courseData).map((node: NodeDefinition) => {
      if (!node.data.id) {
        throw new Error("Node ID is undefined");
      }

      // Handle operator nodes (from astToElements) which use label instead of title
      const label = node.data.label || node.data.title || node.data.id;
      const displayText = labelIsCode ? node.data.id : label;

      return {
        id: node.data.id,
        width: displayText.length * 7.5 + 10, // Added padding
        height: node.data.type === "operator" ? 20 : (labelIsCode ? 15 : 25),
      };
    }),
    edges: getEdgeData(courseData).map((edge: EdgeDefinition) => {
      if (!edge.data) {
        throw new Error("Edge is undefined");
      }
      return {
        id: edge.data.source + "-" + edge.data.target,
        sources: [edge.data.source],
        targets: [edge.data.target],
      };
    }),
  };

  const nodePos = await elk.layout(newLayout);
  return {
    name: "preset",

    positions: Object.fromEntries(
      nodePos.children!.map((child) => [
          child.id,
          {
            x: child.x === undefined ? 0 : child.x,
            y: child.y === undefined ? 0 : child.y,
          },
        ]),
    ),
    animate: animate,
    animationDuration: 1000,
    animationEasing: "ease-in-out",
    zoom: undefined, // the zoom level to set (prob want fit = false if set)
    pan: undefined, // the pan level to set (prob want fit = false if set)
    fit: true, // whether to fit to viewport
    padding: 30, // padding on fit
  };
}

/**
 * Tree layout using ELK's mrtree algorithm with increased spacing
 * to prevent taxi edges from routing through nodes.
 */
export async function generateTreeLayout(
  animate: boolean,
  courseData: ElementDefinition[],
  labelIsCode: boolean,
): Promise<LayoutOptions> {
  const elk = new ELK();

  // Build node dimensions map
  const nodeDimensions = new Map<string, { width: number; height: number }>();

  const children = getNodeData(courseData).map((node: NodeDefinition) => {
    if (!node.data.id) {
      throw new Error("Node ID is undefined");
    }

    const label = node.data.label || node.data.title || node.data.id;
    const displayText = labelIsCode ? label : (node.data.title || label);
    const isOperator = node.data.type === "operator";

    const fontSize = isOperator ? COURSE_GRAPH_OPERATOR_FONT_SIZE : COURSE_GRAPH_FONT_SIZE;
    const textWidth = measureTextWidth(displayText, fontSize);

    const width = textWidth + COURSE_GRAPH_NODE_PADDING_X * 2;
    const height = fontSize + COURSE_GRAPH_NODE_PADDING_Y * 2;

    nodeDimensions.set(node.data.id, { width, height });

    return {
      id: node.data.id,
      width,
      height,
    };
  });

  const newLayout: ElkNode = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "mrtree",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": "20",
      "elk.mrtree.weighting": "CONSTRAINT",
    },
    children,
    edges: getEdgeData(courseData).map((edge: EdgeDefinition) => {
      if (!edge.data) {
        throw new Error("Edge is undefined");
      }
      return {
        id: edge.data.source + "-" + edge.data.target,
        sources: [edge.data.source],
        targets: [edge.data.target],
      };
    }),
  };

  const nodePos = await elk.layout(newLayout);

  // Group nodes by their layer (x position determines layer in horizontal layout)
  // Then align all nodes in each layer to the right edge of that layer
  const layerMap = new Map<number, { id: string; x: number; width: number }[]>();

  for (const child of nodePos.children!) {
    const dims = nodeDimensions.get(child.id!) || { width: 0, height: 0 };
    const x = child.x ?? 0;

    // Round x to group nodes in the same layer
    const layerX = Math.round(x / 10) * 10;

    if (!layerMap.has(layerX)) {
      layerMap.set(layerX, []);
    }
    layerMap.get(layerX)!.push({ id: child.id!, x, width: dims.width });
  }

  // For each layer, find the max right edge and align all nodes to it
  const nodeXAdjustments = new Map<string, number>();

  for (const [, nodes] of layerMap) {
    const maxRightEdge = Math.max(...nodes.map((n) => n.x + n.width));

    for (const node of nodes) {
      const adjustedX = maxRightEdge - node.width;
      nodeXAdjustments.set(node.id, adjustedX);
    }
  }

  // ELK returns top-left positions, but Cytoscape expects center positions
  return {
    name: "preset",
    positions: Object.fromEntries(
      nodePos.children!.map((child) => {
        const dims = nodeDimensions.get(child.id!) || { width: 0, height: 0 };
        const adjustedX = nodeXAdjustments.get(child.id!) ?? (child.x ?? 0);
        return [
          child.id,
          {
            x: adjustedX + dims.width / 2,
            y: (child.y ?? 0) + dims.height / 2,
          },
        ];
      }),
    ),
    animate: animate,
    animationDuration: 1000,
    animationEasing: "ease-in-out",
    zoom: undefined,
    pan: undefined,
    fit: true,
    padding: 30,
  };
}

export function generateFcoseLayout(animate: boolean) {
  return {
    name: "fcose",
    quality: "proof", // 'draft', 'default' or 'proof'
    animate: animate, // Whether to animate the layout
    animationDuration: 1000, // Duration of the animation in milliseconds
    animationEasing: "ease-in-out", // Easing of the animation
    fit: true, // Whether to fit the viewport to the graph
    padding: 30, // Padding around the layout
    nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
    uniformNodeDimensions: true, // Specifies whether the node dimensions should be uniform
    packComponents: true, // Pack connected components - usually for graphs with multiple components
    nodeRepulsion: 40000, // Node repulsion (non overlapping) multiplier
    idealEdgeLength: 60, // Ideal edge (non nested) length
    edgeElasticity: 0.002, // Divisor to compute edge forces
    nestingFactor: 1, // Nesting factor (multiplier) to compute ideal edge length for nested edges
    gravity: 1,
    gravityRangeCompound: 1,
    gravityCompound: 0.1,
    gravityRange: 1.5,
    initialEnergyOnIncremental: 0.1,
    randomize: true, // Whether to randomize the initial positions of nodes
    // fixedNodeConstraint: [
    //     {
    //         nodeId: '300',
    //         position: {x: -100, y: 0}
    //     },
    //     {
    //         nodeId: '400',
    //         position: {x: 100, y: 0}
    //     }
    // ],
    // alignmentConstraint: {
    //     vertical: [],
    //     horizontal: [
    //         ['221', '222'],
    //         ['300', '400']
    //     ]
    // },
    // relativePlacementConstraint: [
    //     {left: '200', right: '300', gap: 100},
    //     {left: '221', right: '222', gap: 200},
    // ]
  };
}
