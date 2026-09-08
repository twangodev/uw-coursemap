<script lang="ts">
  import { SvelteFlow, Controls, Background } from "@xyflow/svelte";
  import "@xyflow/svelte/dist/style.css";
  import RequirementNode from "./RequirementNode.svelte";
  import { visibleTree } from "$lib/requirements";
  import type { Requirements } from "$lib/types";
  let { ast }: { ast: Requirements } = $props();
  let expanded = $state(new Set<string>());
  $effect(() => {
    expanded = new Set(
      ast.nodes
        .filter(
          (n) =>
            n.id === ast.root ||
            ast.nodes.find((r) => r.id === ast.root)?.children?.includes(n.id),
        )
        .map((n) => n.id),
    );
  });
  let graph = $derived(visibleTree(ast, expanded));
  const nodeTypes = { requirement: RequirementNode };
  function toggle(id: string) {
    const next = new Set(expanded);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    expanded = next;
  }
</script>

<div class="graph">
  <SvelteFlow
    nodes={graph.nodes}
    edges={graph.edges}
    {nodeTypes}
    fitView
    zoomOnScroll={false}
    preventScrolling={false}
    minZoom={0.15}
    nodesDraggable={false}
    nodesConnectable={false}
    onnodeclick={({ node }) => toggle(node.id)}
    ><Background /><Controls /></SvelteFlow
  >
</div>
<p class="muted mono">
  Select a group to expand or collapse. Course links are available in the text
  tree.
</p>

<style>
  :global(.svelte-flow) {
    --xy-controls-button-background-color: var(--bg);
    --xy-controls-button-color: var(--text);
    --xy-controls-button-border-color: var(--border);
    --xy-attribution-background-color: var(--bg);
    --xy-background-color: var(--surface);
    --xy-edge-stroke: var(--muted);
  }
  .graph {
    height: 420px;
    border: 1px solid var(--border);
    border-radius: 5px;
    background: var(--surface);
  }
</style>
