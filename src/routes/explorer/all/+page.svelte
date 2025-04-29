<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";

    let { data } = $props();

    let elementDefinitions = $derived(data.elementDefinitions);
    let styleEntries = $derived(data.styleEntries);

</script>

<Cytoscape {elementDefinitions} {styleEntries}/>