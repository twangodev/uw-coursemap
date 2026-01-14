import type { StylesheetStyle } from "cytoscape";
import { getTextColor } from "$lib/theme.ts";

export type StyleEntry = {
  [parent: string]: string;
};

export type GraphType = "department" | "course";

// Course graph layout constants
export const COURSE_GRAPH_FONT_SIZE = 8;
export const COURSE_GRAPH_OPERATOR_FONT_SIZE = 8;
export const COURSE_GRAPH_NODE_PADDING_X = 10;
export const COURSE_GRAPH_NODE_PADDING_Y = 5;

/**
 * Common styles shared between department and course graphs
 */
function getCommonStyles(mode: "light" | "dark" | undefined): StylesheetStyle[] {
  return [
    {
      selector: ".highlighted-nodes",
      style: {
        "border-width": 1,
        "border-color": getTextColor(mode),
        "border-style": "solid",
      },
    },
    {
      selector: ".highlighted-edges",
      style: {
        width: 2,
      },
    },
    {
      selector: ".faded",
      style: {
        opacity: 0.25,
        "text-opacity": 0.25,
      },
    },
    {
      selector: "*",
      style: {
        "transition-property": "opacity",
        "transition-duration": 0.2,
      },
    },
    {
      selector: ".no-overlay",
      style: {
        "overlay-padding": 0,
        "overlay-opacity": 0,
      },
    },
  ];
}

export async function getStyleData(styleUrl: string): Promise<StyleEntry[]> {
  const response = await fetch(styleUrl);
  return await response.json();
}

/**
 * Get styles for department graphs (theme-reactive, uses parent colors)
 */
export function getStyles(
  styleData: StyleEntry[],
  mode: "light" | "dark" | undefined,
  showCode: boolean,
): StylesheetStyle[] {
  let defaultStyles: StylesheetStyle[] = [
    {
      selector: "node",
      style: {
        label: showCode ? "data(id)" : "data(title)",
        "text-valign": "center",
        "text-halign": "center",
        "background-color": "#757575",
        "text-wrap": "wrap",
        "text-max-width": "100", // Forces wrapping for long cross-listed course names
        "text-margin-y": 2,
        color: getTextColor(mode),
      },
    },
    {
      selector: 'node[type="compound"]',
      style: {
        "text-valign": "top",
        "border-width": 0,
        "background-opacity": 0,
        label: "",
      },
    },
    {
      selector: "edge",
      style: {
        width: 1,
        "line-color": getTextColor(mode),
        "curve-style": "straight",
        "target-arrow-color": getTextColor(mode),
        "target-arrow-shape": "triangle",
        "source-distance-from-node": 5,
        "target-distance-from-node": 5,
        "text-wrap": "wrap",
        "font-size": 10,
      },
    },
    {
      selector: ".cy-expand-collapse-collapsed-node",
      style: {
        "overlay-opacity": 0,
        "overlay-color": "transparent",
      },
    },
    {
      selector: "node:parent",
      style: {
        "overlay-opacity": 0,
        "overlay-color": "transparent",
      },
    },
    ...getCommonStyles(mode),
  ];

  const styles = styleData.map((item) => {
    const [parent, color] = Object.entries(item)[0];
    return {
      selector: `node[parent="${parent}"]`,
      style: {
        "background-color": color,
      },
    };
  });

  return defaultStyles.concat(styles);
}

/**
 * Get styles for course graphs (theme-reactive for highlights)
 */
export function getCourseGraphStyles(
  mode: "light" | "dark" | undefined,
): StylesheetStyle[] {
  return [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "background-color": "#757575",
        "text-wrap": "wrap",
        "text-max-width": "100",
        "font-size": COURSE_GRAPH_FONT_SIZE,
        "font-family": "Inter, system-ui, sans-serif",
        "text-outline-width": 0,
        shape: "round-rectangle",
        width: "label",
        height: "label",
        padding: `${COURSE_GRAPH_NODE_PADDING_Y}px ${COURSE_GRAPH_NODE_PADDING_X}px`,
      },
    },
    {
      selector: 'node[type="operator"]',
      style: {
        "background-opacity": 0,
        "text-margin-y": 0,
        color: getTextColor(mode),
      },
    },
    {
      selector: 'node[type="prereq"]',
      style: {
        "background-color": "#f89057",
        color: "#7f3004",
      },
    },
    {
      selector: 'node.taken-nodes[type="prereq"]',
      style: {
        "background-color": "#99cd98",
        color: "#4a7d4a",
      },
    },
    {
      selector: 'node[type="target"]',
      style: {
        "background-color": "#f2777a",
        color: "#8e0e10",
      },
    },
    {
      selector: "edge",
      style: {
        width: 1,
        "line-color": getTextColor(mode),
        "curve-style": "taxi",
        "taxi-direction": "horizontal",
        "taxi-turn": "50%",
        "target-arrow-shape": "none",
        "source-endpoint": "outside-to-node",
        "target-endpoint": "outside-to-node",
      },
    },
    ...getCommonStyles(mode),
  ];
}
