<script lang="ts">
  import type { Requirements } from "$lib/types";
  import {
    nodeLabel,
    requirementTree,
    type RequirementBranch,
  } from "$lib/requirements";
  import { courseUrl, courseTitle } from "$lib/format";
  let {
    ast,
    course,
    following = [],
  }: {
    ast: Requirements;
    course: string;
    following?: { code: string; title: string }[];
  } = $props();
  let tree = $derived(requirementTree(ast));
  let showAll = $state(false);
  let visibleFollowing = $derived(showAll ? following : following.slice(0, 8));
</script>

{#snippet branch(node: RequirementBranch)}
  <li class="relative flex items-center justify-end pr-5 pl-0 branch py-[5px]">
    {#if node.children.length}
      <ul class="list-none p-0 m-0 shrink-0 branches">
        {#each node.children as child}{@render branch(child)}{/each}
      </ul>
      <span
        class="relative shrink-0 ml-5 max-w-37.5 text-[12px] text-muted text-center condition py-[3px] px-2"
        >{node.kind === "all"
          ? "take all"
          : node.kind === "any"
            ? "take one"
            : node.kind === "not"
              ? "not eligible with"
              : nodeLabel(node)}</span
      >
    {:else if node.course}
      <a
        class="block rounded-[999px] bg-accent-soft text-accent text-[13px] leading-[1.4] max-w-57.5 text-center course-node py-[5px] px-2.5"
        href={courseUrl(
          node.course.subjects[0] + " " + node.course.course_number,
        )}>{nodeLabel(node)}</a
      >
    {:else}<span
        class="block max-w-47.5 text-[13px] leading-[1.5] text-right text-node py-1 px-2"
        >{nodeLabel(node)}</span
      >{/if}
  </li>
{/snippet}

<!-- The overflowing tree is keyboard-scrollable. -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
  class="max-w-full overflow-x-auto requirement-tree py-7 px-0"
  role="region"
  aria-label="Prerequisite relationships"
  tabindex="0"
>
  <div
    class="flex items-center w-[max-content] min-w-full justify-center tree-layout py-0 px-3"
  >
    {#if tree}<ul class="list-none p-0 m-0 shrink-0 branches prerequisites">
        {@render branch(tree)}
      </ul>{/if}
    <span
      class="shrink-0 rounded-[999px] bg-accent text-canvas text-[15px] font-[550] max-w-55 text-center current-course py-[9px] px-[15px]"
      >{course}</span
    >
    {#if following.length}
      <span class="shrink-0 text-[12px] text-muted following-label py-0 px-3.5"
        >used by</span
      >
      <ul class="list-none p-0 m-0 shrink-0 branches following">
        {#each visibleFollowing as next}<li
            class="relative flex items-center justify-start pr-0 pl-5 branch py-[5px]"
          >
            <a
              class="block rounded-[999px] bg-accent-soft text-accent text-[13px] leading-[1.4] max-w-57.5 text-center course-node py-[5px] px-2.5"
              href={courseUrl(next.code)}
              title={courseTitle(next.title)}>{next.code}</a
            >
          </li>{/each}
        {#if following.length > 8}<li
            class="relative flex items-center justify-start pr-0 pl-5 branch py-[5px]"
          >
            <button
              class="border-0 text-[12px] text-muted bg-transparent more-courses py-[5px] px-2.5"
              onclick={() => (showAll = !showAll)}
              >{showAll
                ? "Show fewer"
                : `+${following.length - 8} more courses`}</button
            >
          </li>{/if}
      </ul>
    {/if}
  </div>
</div>
{#if following.length || ast.status !== "valid"}<p class="section-note">
    {#if following.length}“Used by” includes alternatives; linked courses may
      have other requirements.
    {/if}
    {#if ast.status !== "valid"}This is a best-effort interpretation; check the
      catalog requirements above.{/if}
  </p>{/if}

<style>
  /* Tree arrangement inspired by NUSMods ModuleTree; see NUSMods.LICENSE. */
  .branch::before {
    content: "";
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    border-right: 1px solid var(--border);
  }
  .branch:first-child::before {
    top: 50%;
  }
  .branch:last-child::before {
    bottom: 50%;
  }
  .branch::after {
    content: "";
    position: absolute;
    right: 0;
    top: 50%;
    width: 20px;
    border-top: 1px solid var(--border);
  }
  .condition::before {
    content: "";
    position: absolute;
    left: -20px;
    top: 50%;
    width: 20px;
    border-top: 1px solid var(--border);
  }
  .following .branch::before {
    left: 0;
    right: auto;
  }
  .following .branch::after {
    left: 0;
    right: auto;
  }
</style>
