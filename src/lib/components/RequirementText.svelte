<script lang="ts">
  import type { Requirements } from "$lib/types";
  import { nodeLabel } from "$lib/requirements";
  let { ast }: { ast: Requirements } = $props();
</script>

{#snippet branch(tree: Requirements, id: string, seen: string[])}{@const node =
    tree.nodes.find((n) => n.id === id)}{#if node && !seen.includes(id)}<li>
      {#if node.course}<a
          href={"/search?q=" +
            encodeURIComponent(
              node.course.subjects[0] + " " + node.course.course_number,
            )}>{nodeLabel(node)}</a
        >{:else}{nodeLabel(node)}{/if}{#if node.children?.length}<ul>
          {#each node.children as child}{@render branch(tree, child, [
              ...seen,
              id,
            ])}{/each}
        </ul>{/if}
    </li>{/if}{/snippet}
<ul class="tree">{@render branch(ast, ast.root, [])}</ul>

<style>
  ul {
    list-style: disc;
    padding-left: 1.4rem;
  }
  li {
    padding: 0.3rem 0;
  }
  .tree > li {
    list-style: none;
  }
  .tree {
    padding-left: 0;
  }
  li ul {
    border-left: 1px solid var(--border);
    margin-left: 0.3rem;
  }
</style>
