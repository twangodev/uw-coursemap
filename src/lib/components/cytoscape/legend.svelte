<script lang="ts">
    import * as Card from "$lib/components/ui/card/index.js";
    import type { StylesheetStyle } from "cytoscape";
    import { Badge } from "../ui/badge";
    import { Button } from "../ui/button";
    interface Props {
        cytoscapeStyles: StylesheetStyle[];
    }
    let { cytoscapeStyles }: Props = $props();
    
    let subjects = cytoscapeStyles.filter(style => style.selector.includes('node[parent=')).map(style => style.selector.match(/parent="([^"]+)"/)![1]);
    let subject_colors = cytoscapeStyles.filter(style => style.selector.includes('node[parent=')).map(style => style.style['background-color']);
    console.log(subject_colors);
</script>

<div class="absolute bottom-4 left-4">
<Card.Root class="px-2 py-1">
    <!-- <Card.Header
        class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
            </Card.Header> -->
    <Card.Content class="p-2 pb-1">
        <Card.Title class="text-base font-medium">Subjects</Card.Title
        >
        {#each subjects as subject, i (subject)}

            <div class="flex flex-row items-center space-x-2">
                <div class="w-4 h-4" style="background-color: {subject_colors[i]}"></div>

                <p class="text-sm break-words">{subject}</p>
            </div>
        {/each}

    </Card.Content>
    <!-- <Card.Header
        class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
    </Card.Header> -->
    <Card.Content class="p-2 pt-1">
        <Card.Title class="text-base font-medium">Options</Card.Title>
        <Button>Show title</Button>
    </Card.Content>
</Card.Root>
</div>