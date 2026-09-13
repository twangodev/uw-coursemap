<script lang="ts">
  import type { Requirements } from "$lib/types";
  import { courseUrl } from "$lib/format";
  import { nodeLabel } from "$lib/requirements";
  let { ast }: { ast: Requirements } = $props();
</script>

{#snippet branch(tree: Requirements, id: string, seen: string[])}{@const node =
    tree.nodes.find((n) => n.id === id)}{#if node && !seen.includes(id)}<li
      class="py-[0.3rem] px-0"
    >
      {#if node.course}<a
          href={courseUrl(
            node.course.subjects[0] + " " + node.course.course_number,
          )}>{nodeLabel(node)}</a
        >{:else}{nodeLabel(node)}{/if}{#if node.children?.length}<ul
          class="list-disc pl-[1.4rem] border-l border-l-border ml-[0.3rem]"
        >
          {#each node.children as child}{@render branch(tree, child, [
              ...seen,
              id,
            ])}{/each}
        </ul>{/if}
    </li>{/if}{/snippet}
<ul class="list-disc pl-0 tree">{@render branch(ast, ast.root, [])}</ul>

<style>
  .tree > li {
    list-style: none;
  }
</style>
