<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import { page } from '$app/state';
    import {env} from "$env/dynamic/public";
    import { onMount } from "svelte";
    import { toast } from "svelte-sonner";

    let subject = $derived(page.params.subject.toUpperCase());

    const PUBLIC_API_URL = env.PUBLIC_API_URL;
    onMount(() => {
        toast.message(`Showing all ${subject} courses`, {
            duration: 5000,
            class: "bg-secondary text-secondary-foreground text-lg font-medium text-center w-full",
            position: "top-center"
        });
    });

</script>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json" />