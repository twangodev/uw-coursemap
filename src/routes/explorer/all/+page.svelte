<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {env} from "$env/dynamic/public";

    const PUBLIC_API_URL = env.PUBLIC_API_URL;

</script>

<Cytoscape url="{PUBLIC_API_URL}/global_graph.json" styleUrl="{PUBLIC_API_URL}/global_style.json"/>