<script lang="ts">
  import type { Requirements } from "$lib/types";
  import { nodeLabel, requirementTree, type RequirementBranch } from "$lib/requirements";
  import { courseUrl, courseTitle } from "$lib/format";
  let { ast, course, following = [] }: { ast: Requirements; course: string; following?: { code: string; title: string }[] } = $props();
  let tree = $derived(requirementTree(ast));
  let showAll = $state(false);
  let visibleFollowing = $derived(showAll ? following : following.slice(0, 8));
</script>

{#snippet branch(node: RequirementBranch)}
  <li class="branch">
    {#if node.children.length}
      <ul class="branches">{#each node.children as child}{@render branch(child)}{/each}</ul>
      <span class="condition">{node.kind === "all" ? "take all" : node.kind === "any" ? "take one" : node.kind === "not" ? "not eligible with" : nodeLabel(node)}</span>
    {:else if node.course}
      <a class="course-node" href={courseUrl(node.course.subjects[0] + " " + node.course.course_number)}>{nodeLabel(node)}</a>
    {:else}<span class="text-node">{nodeLabel(node)}</span>{/if}
  </li>
{/snippet}

<!-- The overflowing tree is keyboard-scrollable. -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div class="requirement-tree" role="region" aria-label="Prerequisite relationships" tabindex="0">
  <div class="tree-layout">
    {#if tree}<ul class="branches prerequisites">{@render branch(tree)}</ul>{/if}
    <span class="current-course">{course}</span>
    {#if following.length}
      <span class="following-label">used by</span>
      <ul class="branches following">
        {#each visibleFollowing as next}<li class="branch"><a class="course-node" href={courseUrl(next.code)} title={courseTitle(next.title)}>{next.code}</a></li>{/each}
        {#if following.length > 8}<li class="branch"><button class="more-courses" onclick={() => showAll = !showAll}>{showAll ? "Show fewer" : `+${following.length - 8} more courses`}</button></li>{/if}
      </ul>
    {/if}
  </div>
</div>
{#if following.length || ast.status !== "valid"}<p class="section-note">
  {#if following.length}“Used by” includes alternatives; linked courses may have other requirements. {/if}
  {#if ast.status !== "valid"}This is a best-effort interpretation; check the catalog requirements above.{/if}
</p>{/if}

<style>
  /* Tree arrangement inspired by NUSMods ModuleTree; see NUSMods.LICENSE. */
  .requirement-tree { max-width: 100%; overflow-x: auto; padding: 28px 0; }
  .tree-layout { display: flex; align-items: center; width: max-content; min-width: 100%; justify-content: center; padding: 0 12px; }
  .branches { list-style: none; padding: 0; margin: 0; flex-shrink: 0; }
  .branch { position: relative; display: flex; align-items: center; justify-content: flex-end; padding: 5px 20px 5px 0; }
  .branch::before { content: ""; position: absolute; right: 0; top: 0; bottom: 0; border-right: 1px solid var(--border); }
  .branch:first-child::before { top: 50%; }
  .branch:last-child::before { bottom: 50%; }
  .branch::after { content: ""; position: absolute; right: 0; top: 50%; width: 20px; border-top: 1px solid var(--border); }
  .condition { position: relative; flex-shrink: 0; margin-left: 20px; padding: 3px 8px; max-width: 150px; font-size: 12px; color: var(--muted); text-align: center; }
  .condition::before { content: ""; position: absolute; left: -20px; top: 50%; width: 20px; border-top: 1px solid var(--border); }
  .course-node { display: block; border-radius: 999px; padding: 5px 10px; background: var(--accent-soft); color: var(--accent); font-size: 13px; line-height: 1.4; max-width: 230px; text-align: center; }
  .text-node { display: block; max-width: 190px; padding: 4px 8px; font-size: 13px; line-height: 1.5; text-align: right; }
  .current-course { flex-shrink: 0; padding: 9px 15px; border-radius: 999px; background: var(--accent); color: var(--bg); font-size: 15px; font-weight: 550; max-width: 220px; text-align: center; }
  .following-label { padding: 0 14px; flex-shrink: 0; font-size: 12px; color: var(--muted); }
  .following .branch { justify-content: flex-start; padding: 5px 0 5px 20px; }
  .following .branch::before { left: 0; right: auto; }
  .following .branch::after { left: 0; right: auto; }
  .more-courses { padding: 5px 10px; border: 0; font-size: 12px; color: var(--muted); background: transparent; }
</style>
