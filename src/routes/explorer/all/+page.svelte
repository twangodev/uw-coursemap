<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {PUBLIC_API_URL} from "$env/static/public";

</script>

<Cytoscape url="{PUBLIC_API_URL}/global_graph.json" styleUrl="{PUBLIC_API_URL}/global_style.json"/>