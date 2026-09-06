<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";
  import SubjectCardGrid from "$lib/components/subject-card-grid.svelte";
  import { m } from "$lib/paraglide/messages";

  let { data } = $props();

  let { subjects } = $derived(data);
</script>

<ContentWrapper>
  <PageHeader>
    <PageHeaderHeading>{m["stats.title"]()}</PageHeaderHeading>
    <PageHeaderDescription class="text-muted-foreground">
      {m["stats.description"]()}
    </PageHeaderDescription>
  </PageHeader>
  <section class="my-8">
    <SubjectCardGrid {subjects} />
  </section>
</ContentWrapper>
