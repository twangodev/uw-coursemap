<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import { page } from '$app/state';
    import {PUBLIC_API_URL} from "$env/static/public";

    let subject = $derived(page.params.subject.toUpperCase());


</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json" />