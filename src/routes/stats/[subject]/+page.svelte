<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";
</script>

<ContentWrapper>
  <PageHeader>
    <PageHeaderHeading>Coming Soon?</PageHeaderHeading>
    <PageHeaderDescription class="text-muted-foreground">
      Haven't had time to implement this yet, see <a
        href="https://github.com/twangodev/uw-coursemap/issues/782">#782</a
      >
    </PageHeaderDescription>
  </PageHeader>
</ContentWrapper>
