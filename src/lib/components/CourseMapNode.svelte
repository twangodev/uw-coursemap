<script lang="ts">
  import { courseTitle } from "$lib/format";
  import { Handle, Position } from "@xyflow/svelte";
  let { data } = $props();
</script>

<Handle type="target" position={Position.Left} style="top: 12px; left: calc(50% - 10px); opacity: 0" />
<div class="map-node" class:focused={data.focused}>
  <span class="mono">{data.code}</span>
  <a
    href={data.href}
    class="nodrag"
    onclick={(event) => event.stopPropagation()}>{courseTitle(data.title)} ↗</a
  >
</div>
<Handle type="source" position={Position.Right} style="top: 12px; left: calc(50% + 10px); opacity: 0" />

<style>
  .map-node::before { content: ""; position: absolute; left: calc(50% - 10px); top: 2px; width: 20px; height: 20px; border-radius: 50%; border: 2px solid var(--accent); background: var(--bg); }

  .map-node {
    width: 230px;
    padding: 34px 8px 0;
    display: grid;
    gap: 4px;
    background: transparent;
    position: relative;
    text-align: center;

    color: var(--text);
    font-size: 13px;
  }
  .focused::before { background: var(--accent); box-shadow: 0 0 0 5px var(--accent-soft); }
  .focused {
    font-weight: 550;
  }
  .mono {
    color: var(--accent);
    font-size: 12px;
  }
  .mono, a { position: relative; width: fit-content; max-width: 100%; margin-inline: auto; padding-inline: 3px; background: var(--surface); }
  a {
    line-height: 1.5;
  }
</style>
