<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {env} from "$env/dynamic/public";

    const PUBLIC_API_URL = env.PUBLIC_API_URL;

</script>

<!-- Banner showing which course graph is shown -->
<div class="absolute left-0 right-0 bg-secondary py-2 z-10">
    <div class="container mx-auto flex justify-center items-center">
        <h2 class="text-lg font-medium text-secondary-foreground whitespace-nowrap">
            Showing all courses
        </h2>
    </div>
</div>

<Cytoscape url="{PUBLIC_API_URL}/global_graph.json" styleUrl="{PUBLIC_API_URL}/global_style.json"/>