<script lang="ts">

    import {page} from "$app/stores";
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header/index.js";

    let error = $derived($page.error);

</script>

<ContentWrapper>
    <PageHeader>
        <PageHeaderHeading>Error {$page.status}</PageHeaderHeading>
        <PageHeaderDescription>{error?.message}</PageHeaderDescription>
    </PageHeader>
</ContentWrapper>

