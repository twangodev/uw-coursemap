<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/Cytoscape.svelte";
    import { page } from '$app/stores';
    import {PUBLIC_API_URL} from "$env/static/public";

    $: subject = $page.params.subject;

</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject.toUpperCase()}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject.toUpperCase()}.json"/>