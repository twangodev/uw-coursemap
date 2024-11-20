<script lang="ts">

    import Cytoscape from "$lib/components/Cytoscape.svelte";
    import { page } from '$app/stores';
    import {PUBLIC_API_URL} from "$env/static/public";

    $: subject = $page.params.subject;

</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json"/>