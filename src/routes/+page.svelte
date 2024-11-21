<script lang="ts">
    import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header/index.js";
    import {Button, buttonVariants} from "$lib/components/ui/button";

</script>

<ContentWrapper>
    <PageHeader>
        <PageHeaderHeading>Course exploration, made easy</PageHeaderHeading>
        <PageHeaderDescription class="text-muted-foreground">
            Explore the courses offered by the UW-Madison in a visual and interactive way.
        </PageHeaderDescription>
        <p class="text-center text-sm text-primary">
            UW Course Map is not affiliated by the University of Wisconsin-Madison.
        </p>
        <div class="flex w-full items-center justify-center space-x-4 py-4 md:pb-10">
            <Button href="/explorer">
                Get Started
            </Button>
        </div>
    </PageHeader>
</ContentWrapper>
