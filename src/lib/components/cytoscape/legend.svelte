<script lang="ts">
  import type { StyleEntry } from "$lib/components/cytoscape/graph-styles.ts";

  interface Props {
    styleEntries: StyleEntry[];
    hiddenSubject?: string | null;
  }

  let { styleEntries, hiddenSubject = $bindable(null) }: Props = $props();
</script>

<div class="absolute bottom-4 left-4">
  {#each styleEntries as entry}
    {#each Object.entries(entry) as [subject, hex]}
      {@const enabled = subject !== hiddenSubject}
      <div
        class="my-1 flex flex-row items-center space-x-2 {enabled
          ? 'opacity-100'
          : 'opacity-50'}"
      >
        <button
          class="h-4 w-4 cursor-pointer rounded-full"
          aria-label="Show/Hide {subject}"
          style="background-color: {hex}"
          onclick={() => {
            hiddenSubject = hiddenSubject === subject ? null : subject;
          }}
        ></button>
        <span class="text-sm select-none">{subject}</span>
      </div>
    {/each}
  {/each}
  <!--<Card.Root class="px-2 py-1">-->
  <!--    <Card.Content class="p-2 pb-1">-->
  <!--    -->
  <!--    </Card.Content>-->
  <!--    &lt;!&ndash; <Card.Header-->
  <!--        class="flex flex-row items-center justify-between space-y-0 pb-2"-->
  <!--    >-->
  <!--    </Card.Header> &ndash;&gt;-->
  <!--</Card.Root>-->
</div>
