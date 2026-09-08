<script lang="ts">
  import { Handle, Position } from "@xyflow/svelte";
  let { data } = $props();
</script>

<Handle type="target" position={Position.Left} style="top: 12px; left: calc(50% - 10px); opacity: 0" />
<div class="node" class:group={data.expandable}>
  {#if data.course}<a
      class="nodrag"
      href={"/search?q=" +
        encodeURIComponent(
          data.course.subjects[0] + " " + data.course.course_number,
        )}
      onclick={(event) => event.stopPropagation()}>{data.label}</a
    >{:else}<span>{data.label}</span>{/if}{#if data.expandable}<span
      class="mono muted">{data.expanded ? "− collapse" : "+ expand"}</span
    >{/if}
</div>
<Handle type="source" position={Position.Right} style="top: 12px; left: calc(50% + 10px); opacity: 0" />

<style>
  .node::before { content: ""; position: absolute; left: calc(50% - 10px); top: 2px; width: 20px; height: 20px; border-radius: 50%; border: 2px solid var(--accent); background: var(--bg); }

  .node {
    width: 190px;
    min-height: 54px;
    padding: 34px 8px 0;
    position: relative;
    text-align: center;

    background: transparent;
    color: var(--text);
    display: grid;
    gap: 0.4rem;
    font-size: 14px;
  }
  .node.group::before { border-color: var(--muted); background: var(--surface); }
  .node.group {
    width: 190px;
    font-size: 13px;
  }
  .node.group .mono {
    font-size: 10px;
  }
</style>
