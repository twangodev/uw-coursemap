<script lang="ts">
  import { SvelteFlow, Controls, Background } from "@xyflow/svelte";
  import "@xyflow/svelte/dist/style.css";
  import CourseMapNode from "./CourseMapNode.svelte";
  import { mapView, type CourseMapData } from "$lib/course-map";
  let { data, focus }: { data: CourseMapData; focus: string } = $props();
  let selected = $state("");
  $effect(() => {
    selected = focus;
  });
  let graph = $derived(mapView(data, selected));
  const nodeTypes = { course: CourseMapNode };
</script>

<div class="map" aria-label="Course prerequisite map">
  {#key selected}<SvelteFlow
      nodes={graph.nodes}
      edges={graph.edges}
      {nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.18, minZoom: 0.85, maxZoom: 1 }}
      minZoom={0.1}
      nodesDraggable={false}
      nodesConnectable={false}
      zoomOnScroll={false}
      preventScrolling={false}
      onnodeclick={({ node }) => (selected = node.id)}
      ><Background /><Controls /></SvelteFlow
    >{/key}
</div>
<p class="muted">
  {graph.nodes.length - 1} connected courses. Drag to see more.
  Prerequisites on the left; courses that reference this course on the right.
  Select a card to explore its connections, or its title to open the course.
</p>

<style>
  .map {
    height: 620px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface);
  }
  p {
    font-size: 13px;
    line-height: 1.7;
    margin-top: 16px;
  }
  :global(.svelte-flow) {
    --xy-controls-button-background-color: var(--bg);
    --xy-controls-button-color: var(--text);
    --xy-controls-button-border-color: var(--border);
    --xy-edge-stroke: var(--muted);
    --xy-background-color: var(--surface);
  }
  @media (max-width: 640px) {
    .map {
      height: 520px;
    }
  }
</style>
