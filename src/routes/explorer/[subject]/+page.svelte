<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import { page } from '$app/state';
    import {env} from "$env/dynamic/public";

    let subject = $derived(page.params.subject.toUpperCase());

    const PUBLIC_API_URL = env.PUBLIC_API_URL;


</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json" />