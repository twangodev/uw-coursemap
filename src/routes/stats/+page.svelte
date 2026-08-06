<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";
  import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import { m } from "$lib/paraglide/messages";
  import { localizeHref } from "$lib/paraglide/runtime";

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
    <div
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
    >
      {#each subjects as [code, name]}
        <a href={localizeHref(`/stats/${code}`)} class="flex h-full w-full">
          <Card class="flex h-full w-full flex-col">
            <CardHeader>
              <CardTitle class="truncate">{name}</CardTitle>
              <CardDescription class="truncate font-bold">
                {code}
              </CardDescription>
            </CardHeader>
          </Card>
        </a>
      {/each}
    </div>
  </section>
</ContentWrapper>
