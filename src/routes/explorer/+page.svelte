<script lang="ts">

    import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header";
    import {Button} from "$lib/components/ui/button";
    import Search from "$lib/components/Search.svelte";
    import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
    import {goto} from "$app/navigation";

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
            <AlertDialog.Root>
                <AlertDialog.Trigger asChild let:builder>
                    <Button builders={[builder]} variant="outline">Graph All</Button>
                </AlertDialog.Trigger>
                <AlertDialog.Content>
                    <AlertDialog.Header>
                        <AlertDialog.Title>Are you absolutely sure?</AlertDialog.Title>
                        <AlertDialog.Description>
                            Graphing all courses and programs may take a long time and may cause your browser to become unresponsive.
                        </AlertDialog.Description>
                    </AlertDialog.Header>
                    <AlertDialog.Footer>
                        <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
                        <AlertDialog.Action on:click={() => goto('/explorer/all')}>Continue</AlertDialog.Action>
                    </AlertDialog.Footer>
                </AlertDialog.Content>
            </AlertDialog.Root>
        </div>
    </PageHeader>
</ContentWrapper>