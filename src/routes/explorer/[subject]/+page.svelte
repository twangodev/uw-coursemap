<script lang="ts">

    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import { page } from '$app/state';
    import {env} from "$env/dynamic/public";
    import { PageHeader, PageHeaderHeading } from "$lib/components/page-header";
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";

    let subject = $derived(page.params.subject.toUpperCase());

    const PUBLIC_API_URL = env.PUBLIC_API_URL;
</script>

<!-- Banner showing which course graph is shown -->
<div class="absolute left-0 right-0 bg-secondary py-2 z-10">
    <div class="container mx-auto flex justify-center items-center">
        <h2 class="text-lg font-medium text-secondary-foreground whitespace-nowrap">
            Showing all {subject} courses
        </h2>
    </div>
</div>

<Cytoscape url="{PUBLIC_API_URL}/graphs/{subject}.json" styleUrl="{PUBLIC_API_URL}/styles/{subject}.json" />