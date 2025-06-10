<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import type { StylesheetStyle } from "cytoscape";
  import { Badge } from "../ui/badge";
  import { Button } from "../ui/button";
  import ColorDot from "./color-dot.svelte";
  import type { StyleEntry } from "$lib/components/cytoscape/graph-styles.ts";

  interface Props {
    styleEntries: StyleEntry[];
    hiddenSubject: string | null;
  }

  let { styleEntries, hiddenSubject = $bindable(null) }: Props = $props();
</script>

<div class="absolute bottom-4 left-4">
  {#each styleEntries as entry}
    {#each Object.entries(entry) as [subject, hex]}
      <ColorDot
        {hex}
        onclick={() => {
          hiddenSubject = hiddenSubject === subject ? null : subject;
        }}
        label={subject}
        {hiddenSubject}
      />
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
