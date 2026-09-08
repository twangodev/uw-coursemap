<script lang="ts">
  import { courseTitle } from "$lib/format";
  import { Handle, Position } from "@xyflow/svelte";
  let { data } = $props();
</script>

<Handle type="target" position={Position.Left} />
<div class="map-node" class:focused={data.focused}>
  <span class="mono">{data.code}</span>
  <a
    href={data.href}
    class="nodrag"
    onclick={(event) => event.stopPropagation()}>{courseTitle(data.title)} ↗</a
  >
</div>
<Handle type="source" position={Position.Right} />

<style>
  .map-node {
    width: 230px;
    padding: 14px;
    display: grid;
    gap: 8px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    color: var(--text);
    font-size: 13px;
  }
  .focused {
    border-color: var(--accent);
  }
  .mono {
    color: var(--accent);
    font-size: 12px;
  }
  a {
    line-height: 1.5;
  }
</style>
