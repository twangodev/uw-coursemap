import type { ElkNode } from "elkjs/lib/elk-api";
import type { CourseMapData } from "./course-map";

/** The original department map's left-to-right layered layout. */
export function layeredGraph(data: CourseMapData): ElkNode {
  return {
    id: "courses",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.randomSeed": "42",
      "elk.separateConnectedComponents": "true",
      "elk.aspectRatio": "1.5",
      "elk.spacing.nodeNode": "14",
      "elk.layered.spacing.nodeNodeBetweenLayers": "50",
      "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
    },
    children: data.courses.map(course => ({
      id: course.uid,
      width: Math.max(85, course.code.length * 7 + 12),
      height: 22,
    })),
    edges: data.edges.map(edge => ({
      id: `${edge.source}:${edge.target}`,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };
}
