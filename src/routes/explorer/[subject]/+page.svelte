<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/Cytoscape.svelte";
    import { page } from '$app/state';
    import {PUBLIC_API_URL} from "$env/static/public";

    let subject = $derived(page.params.subject.toUpperCase());

    let focus = $derived(page.url.searchParams.get('focus'));

</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json" requestedFocus={focus}/>