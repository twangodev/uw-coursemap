<script lang="ts">
  import { Handle, Position } from "@xyflow/svelte";
  let { data } = $props();
</script>

<Handle type="target" position={Position.Left} />
<div class="node">
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
<Handle type="source" position={Position.Right} />

<style>
  .node {
    width: 245px;
    min-height: 65px;
    padding: 0.7rem 1rem;
    border: 1px solid var(--border);
    border-radius: 5px;
    background: var(--bg);
    color: var(--text);
    display: grid;
    gap: 0.4rem;
    font-size: 14px;
  }
</style>
