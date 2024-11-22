<script lang="ts">

    import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header";
    import {Button} from "$lib/components/ui/button";
    import Search from "$lib/components/Search.svelte";

</script>

<ContentWrapper>
    <PageHeader>
        <PageHeaderHeading>Explorer</PageHeaderHeading>
        <PageHeaderDescription class="text-muted-foreground">
            Start by looking up a course or program offered by the University of Wisconsin-Madison.
        </PageHeaderDescription>
        <p class="text-center text-sm text-primary">
            UW Course Map is not affiliated by the University of Wisconsin-Madison.
        </p>
        <div class="flex w-full items-center justify-center space-x-4 py-4 md:pb-10">
            <Search wide={true}/>
            <Button variant="outline">Graph All</Button>
        </div>
    </PageHeader>
</ContentWrapper>