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

// Space reserved for expand button to the left of leaf nodes
const EXPAND_NODE_SPACE = 40;

/**
 * Compute node dimensions based on label text
 */
function computeNodeDimensions(
  courseData: ElementDefinition[],
  labelIsCode: boolean
): Map<string, { width: number; height: number }> {
  const nodeDimensions = new Map<string, { width: number; height: number }>();

  for (const node of getNodeData(courseData)) {
    if (!node.data.id) continue;

    const label = node.data.label || node.data.title || node.data.id;
    const displayText = labelIsCode ? label : (node.data.title || label);
    const isOperator = node.data.type === "operator";

    const fontSize = isOperator ? COURSE_GRAPH_OPERATOR_FONT_SIZE : COURSE_GRAPH_FONT_SIZE;
    const textWidth = measureTextWidth(displayText, fontSize);

    const width = textWidth + COURSE_GRAPH_NODE_PADDING_X * 2;
    const height = fontSize + COURSE_GRAPH_NODE_PADDING_Y * 2;

    nodeDimensions.set(node.data.id, { width, height });
  }

  return nodeDimensions;
}

/**
 * Add extra width to leaf prereq nodes for ELK layout.
 * This reserves space for expand buttons without affecting visual alignment.
 */
function addExpandSpaceForElk(
  nodeDimensions: Map<string, { width: number; height: number }>,
  courseData: ElementDefinition[]
): Map<string, { width: number; height: number }> {
  // Find nodes with incoming edges (not leaf nodes)
  const nodesWithIncomingEdges = new Set<string>();
  for (const edge of getEdgeData(courseData)) {
    if (edge.data?.target) {
      nodesWithIncomingEdges.add(edge.data.target);
    }
  }

  const elkDimensions = new Map<string, { width: number; height: number }>();

  for (const node of getNodeData(courseData)) {
    if (!node.data.id) continue;

    const dims = nodeDimensions.get(node.data.id)!;
    const isPrereq = node.data.type === "prereq";
    const isLeaf = !nodesWithIncomingEdges.has(node.data.id);

    if (isPrereq && isLeaf) {
      elkDimensions.set(node.data.id, {
        width: dims.width + EXPAND_NODE_SPACE,
        height: dims.height,
      });
    } else {
      elkDimensions.set(node.data.id, dims);
    }
  }

  return elkDimensions;
}

/**
 * Run ELK layered layout and return raw positions (top-left)
 */
async function runElkLayout(
  courseData: ElementDefinition[],
  nodeDimensions: Map<string, { width: number; height: number }>
): Promise<Map<string, { x: number; y: number }>> {
  const elk = new ELK();

  const children = getNodeData(courseData).map((node: NodeDefinition) => {
    const dims = nodeDimensions.get(node.data.id!);
    return {
      id: node.data.id!,
      width: dims!.width,
      height: dims!.height,
    };
  });

  const elkLayout: ElkNode = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": "8",
      "elk.layered.spacing.nodeNodeBetweenLayers": "40",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
      "elk.layered.layering.strategy": "LONGEST_PATH",
      // Crossing minimization to reduce edge overlaps
      "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
      // Better node ordering within layers
      "elk.layered.crossingMinimization.semiInteractive": "true",
      // Edge spacing to avoid collisions
      "elk.layered.spacing.edgeNodeBetweenLayers": "15",
      "elk.layered.spacing.edgeEdgeBetweenLayers": "10",
    },
    children,
    edges: getEdgeData(courseData).map((edge: EdgeDefinition) => ({
      id: edge.data!.source + "-" + edge.data!.target,
      sources: [edge.data!.source],
      targets: [edge.data!.target],
    })),
  };

  const result = await elk.layout(elkLayout);

  const positions = new Map<string, { x: number; y: number }>();
  for (const child of result.children || []) {
    positions.set(child.id!, { x: child.x ?? 0, y: child.y ?? 0 });
  }

  return positions;
}

/**
 * Build incoming edges map (target -> sources[])
 */
function buildIncomingEdgesMap(courseData: ElementDefinition[]): Map<string, string[]> {
  const incomingEdges = new Map<string, string[]>();
  for (const edge of getEdgeData(courseData)) {
    if (edge.data) {
      const sources = incomingEdges.get(edge.data.target) || [];
      sources.push(edge.data.source);
      incomingEdges.set(edge.data.target, sources);
    }
  }
  return incomingEdges;
}

/**
 * Find the root node (node with no outgoing edges)
 */
function findRootNode(courseData: ElementDefinition[]): string | undefined {
  const allTargets = new Set(getEdgeData(courseData).map(e => e.data?.target).filter(Boolean));
  const allSources = new Set(getEdgeData(courseData).map(e => e.data?.source).filter(Boolean));
  const rootNodes = [...allTargets].filter(id => !allSources.has(id));
  return rootNodes[0];
}

/**
 * Compute depth of each node as the longest path from the root.
 * This ensures nodes that appear in multiple paths are placed at their
 * farthest distance, aligning with ELK's LONGEST_PATH layering strategy.
 *
 * Handles cycles in the graph by ignoring back-edges during DFS traversal.
 */
function computeNodeDepths(
  rootId: string,
  incomingEdges: Map<string, string[]>
): Map<string, number> {
  const nodeDepths = new Map<string, number>();
  const visiting = new Set<string>(); // Currently in DFS stack (for cycle detection)

  // DFS to compute longest path, ignoring back-edges (cycles)
  function dfs(nodeId: string, depth: number): void {
    // Cycle detected - skip this edge
    if (visiting.has(nodeId)) {
      return;
    }

    // Update depth if this path is longer
    const existingDepth = nodeDepths.get(nodeId) ?? -1;
    if (depth <= existingDepth) {
      return; // Already found a longer or equal path
    }

    nodeDepths.set(nodeId, depth);
    visiting.add(nodeId);

    // Get predecessors (nodes that have edges pointing to this node)
    const sources = incomingEdges.get(nodeId) || [];
    for (const sourceId of sources) {
      dfs(sourceId, depth + 1);
    }

    visiting.delete(nodeId);
  }

  dfs(rootId, 0);

  return nodeDepths;
}

/**
 * Right-align nodes within each depth layer
 */
function rightAlignLayers(
  positions: Map<string, { x: number; y: number }>,
  nodeDimensions: Map<string, { width: number; height: number }>,
  nodeDepths: Map<string, number>,
  courseData: ElementDefinition[]
): void {
  // Group nodes by depth
  const layerMap = new Map<number, string[]>();
  for (const [nodeId, depth] of nodeDepths) {
    if (!layerMap.has(depth)) layerMap.set(depth, []);
    layerMap.get(depth)!.push(nodeId);
  }

  // Identify operator nodes (no border adjustment needed)
  const operatorNodeIds = new Set<string>();
  for (const node of getNodeData(courseData)) {
    if (node.data.type === "operator") {
      operatorNodeIds.add(node.data.id!);
    }
  }

  // Right-align each layer
  for (const [, nodeIds] of layerMap) {
    const maxRightEdge = Math.max(
      ...nodeIds.map((id) => {
        const pos = positions.get(id)!;
        const dims = nodeDimensions.get(id) || { width: 0, height: 0 };
        return pos.x + dims.width;
      })
    );

    for (const nodeId of nodeIds) {
      const pos = positions.get(nodeId)!;
      const dims = nodeDimensions.get(nodeId) || { width: 0, height: 0 };
      const isOperator = operatorNodeIds.has(nodeId);
      const borderOffset = isOperator ? 0 : 1;
      pos.x = maxRightEdge - dims.width + borderOffset;
    }
  }
}

/**
 * Compress nodes on the same branch vertically
 */
function compressBranches(
  positions: Map<string, { x: number; y: number }>,
  nodeDimensions: Map<string, { width: number; height: number }>,
  nodeDepths: Map<string, number>,
  courseData: ElementDefinition[]
): void {
  const BRANCH_SPACING = 3;

  // Build source -> target map
  const nodeTargets = new Map<string, string>();
  for (const edge of getEdgeData(courseData)) {
    if (edge.data) {
      nodeTargets.set(edge.data.source, edge.data.target);
    }
  }

  // Group nodes by depth
  const layerMap = new Map<number, string[]>();
  for (const [nodeId, depth] of nodeDepths) {
    if (!layerMap.has(depth)) layerMap.set(depth, []);
    layerMap.get(depth)!.push(nodeId);
  }

  for (const [, nodeIds] of layerMap) {
    // Group by target
    const targetGroups = new Map<string, string[]>();
    for (const nodeId of nodeIds) {
      const target = nodeTargets.get(nodeId) || "none";
      if (!targetGroups.has(target)) targetGroups.set(target, []);
      targetGroups.get(target)!.push(nodeId);
    }

    for (const [, groupNodeIds] of targetGroups) {
      if (groupNodeIds.length <= 1) continue;

      // Sort by y position
      groupNodeIds.sort((a, b) => positions.get(a)!.y - positions.get(b)!.y);

      // Calculate center y
      const firstY = positions.get(groupNodeIds[0])!.y;
      const lastY = positions.get(groupNodeIds[groupNodeIds.length - 1])!.y;
      const centerY = (firstY + lastY) / 2;

      // Calculate total height
      let totalHeight = 0;
      for (const nodeId of groupNodeIds) {
        totalHeight += nodeDimensions.get(nodeId)?.height || 0;
      }
      totalHeight += (groupNodeIds.length - 1) * BRANCH_SPACING;

      // Position nodes centered around centerY
      let currentY = centerY - totalHeight / 2;
      for (const nodeId of groupNodeIds) {
        positions.get(nodeId)!.y = currentY;
        currentY += (nodeDimensions.get(nodeId)?.height || 0) + BRANCH_SPACING;
      }
    }
  }
}

/**
 * Center root node relative to its predecessors
 */
function centerRootNode(
  rootId: string,
  positions: Map<string, { x: number; y: number }>,
  nodeDimensions: Map<string, { width: number; height: number }>,
  incomingEdges: Map<string, string[]>
): void {
  const rootPredecessors = incomingEdges.get(rootId) || [];
  if (rootPredecessors.length === 0) return;

  let predMinY = Infinity;
  let predMaxY = -Infinity;
  for (const predId of rootPredecessors) {
    const dims = nodeDimensions.get(predId) || { width: 0, height: 0 };
    const pos = positions.get(predId);
    if (pos) {
      predMinY = Math.min(predMinY, pos.y);
      predMaxY = Math.max(predMaxY, pos.y + dims.height);
    }
  }
  const predCenterY = (predMinY + predMaxY) / 2;

  const rootDims = nodeDimensions.get(rootId) || { width: 0, height: 0 };
  const rootPos = positions.get(rootId);
  if (rootPos) {
    const rootCenterY = rootPos.y + rootDims.height / 2;
    rootPos.y += predCenterY - rootCenterY;
  }
}

/**
 * Convert top-left positions to center positions for Cytoscape
 */
function convertToCenterPositions(
  positions: Map<string, { x: number; y: number }>,
  nodeDimensions: Map<string, { width: number; height: number }>
): Map<string, { x: number; y: number }> {
  const centerPositions = new Map<string, { x: number; y: number }>();
  for (const [nodeId, pos] of positions) {
    const dims = nodeDimensions.get(nodeId) || { width: 0, height: 0 };
    centerPositions.set(nodeId, {
      x: pos.x + dims.width / 2,
      y: pos.y + dims.height / 2,
    });
  }
  return centerPositions;
}

/**
 * Tree layout using ELK's layered algorithm.
 * Modular design: computes dimensions, runs ELK, then applies adjustments.
 */
export async function generateTreeLayout(
  animate: boolean,
  courseData: ElementDefinition[],
  labelIsCode: boolean,
): Promise<LayoutOptions> {
  // 1. Compute node dimensions (visual)
  const nodeDimensions = computeNodeDimensions(courseData, labelIsCode);

  // 2. Add expand space for leaf nodes (ELK only)
  const elkDimensions = addExpandSpaceForElk(nodeDimensions, courseData);

  // 3. Run ELK layout with expanded dimensions
  const positions = await runElkLayout(courseData, elkDimensions);

  // 4. Build graph structure info
  const incomingEdges = buildIncomingEdgesMap(courseData);
  const rootId = findRootNode(courseData);

  if (!rootId) {
    return { name: "preset", positions: {}, animate };
  }

  const nodeDepths = computeNodeDepths(rootId, incomingEdges);

  // 5. Apply adjustments (using visual dimensions, not ELK dimensions)
  rightAlignLayers(positions, nodeDimensions, nodeDepths, courseData);
  compressBranches(positions, nodeDimensions, nodeDepths, courseData);
  centerRootNode(rootId, positions, nodeDimensions, incomingEdges);

  // 6. Convert to center positions
  const centerPositions = convertToCenterPositions(positions, nodeDimensions);

  return {
    name: "preset",
    positions: Object.fromEntries(centerPositions),
    animate,
    animationDuration: 1000,
    animationEasing: "ease-in-out",
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
