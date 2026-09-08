import cytoscape from "cytoscape";
import fcose from "cytoscape-fcose";
import type { CourseMapData } from "./course-map";

cytoscape.use(fcose);

// Layout runs outside the UI thread, including for the complete catalog.
self.onmessage = ({ data }: MessageEvent<{ courses: { uid: string }[]; edges: CourseMapData["edges"] }>) => {
  const cy = cytoscape({
    headless: true,
    styleEnabled: true,
    elements: [
      ...data.courses.map(course => ({ data: { id: course.uid } })),
      ...data.edges.map(edge => ({ data: { ...edge, id: `${edge.source}:${edge.target}` } })),
    ],
    style: [{ selector: "node", style: { width: 110, height: 50 } }],
  });
  try {
    const options: fcose.FcoseLayoutOptions = {
      name: "fcose",
      quality: "default",
      animate: false,
      randomize: true,
      fit: false,
      nodeRepulsion: () => 12000,
      idealEdgeLength: () => 90,
      numIter: data.courses.length > 2000 ? 1000 : 2500,
      tile: true,
      tilingPaddingHorizontal: 35,
      tilingPaddingVertical: 35,
    };
    cy.layout(options).run();
    self.postMessage({ positions: Object.fromEntries(cy.nodes().map(node => [node.id(), node.position()])) });
  } catch (error) {
    self.postMessage({ error: error instanceof Error ? error.message : "Unable to arrange this map." });
  } finally {
    cy.destroy();
  }
};
