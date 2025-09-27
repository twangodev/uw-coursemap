<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";
  import Search from "$lib/components/search.svelte";
  import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import { Award, UserPen, Waypoints, Cookie } from "@lucide/svelte";
  import Github from "$lib/components/icons/github.svelte";
  import { m } from "$lib/paraglide/messages";
  import { localizeHref } from "$lib/paraglide/runtime";

  let { data } = $props();

  let { subjects } = $derived(data);
</script>

<ContentWrapper>
  <PageHeader>
    <PageHeaderHeading>{m["explorer.title"]()}</PageHeaderHeading>
    <PageHeaderDescription class="text-muted-foreground">
      {m["explorer.description"]()}
    </PageHeaderDescription>
    <p class="text-primary text-center text-sm">
      {m["site.disclaimer"]()}
    </p>
    <div
      class="flex w-full items-center justify-center space-x-4 py-4 md:pb-10"
    >
      <Search fake={true} wide={true} />
    </div>
  </PageHeader>
  <section class="my-4">
    <div class="my-8">
      <h2 class="my-2 text-4xl font-bold">{m["explorer.frequentlyVisited.title"]()}</h2>
      <p class="text-muted-foreground">
        {m["explorer.frequentlyVisited.description"]()}
      </p>
    </div>
    <div
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
    >
      <a href={localizeHref("/courses/easiest")} class="flex h-full">
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex truncate">
              <Award class="mr-2 size-4" />
              {m["explorer.cards.easiestCourses.title"]()}
            </CardTitle>
          </CardHeader>
          <CardDescription class="px-6">
            {m["explorer.cards.easiestCourses.description"]()}
          </CardDescription>
        </Card>
      </a>
      <a href={localizeHref("/instructors/by-rating-count")} class="flex h-full">
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex truncate">
              <UserPen class="mr-2 size-4" />
              {m["explorer.cards.mostRatedInstructors.title"]()}
            </CardTitle>
          </CardHeader>
          <CardDescription class="px-6">
            {m["explorer.cards.mostRatedInstructors.description"]()}
          </CardDescription>
        </Card>
      </a>
      <a href={localizeHref("/explorer/all")} class="flex h-full">
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex truncate">
              <Waypoints class="mr-2 size-4" />
              {m["explorer.cards.universityGraph.title"]()}
            </CardTitle>
          </CardHeader>
          <CardDescription class="px-6">
            {m["explorer.cards.universityGraph.description"]()}
          </CardDescription>
        </Card>
      </a>
      <a
        href="https://github.com/twangodev/uw-coursemap/issues"
        class="flex h-full"
      >
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex truncate">
              <Github class="mr-2 size-4" />
              {m["explorer.cards.requestFeature.title"]()}
            </CardTitle>
          </CardHeader>
          <CardDescription class="px-6">
            {m["explorer.cards.requestFeature.description"]()}
          </CardDescription>
        </Card>
      </a>
    </div>
  </section>
  <!--    <section>-->
  <!--        <div class="my-8">-->
  <!--            <h2 class="text-4xl font-bold my-2">Departmental Statistics</h2>-->
  <!--            <p class="text-muted-foreground">-->
  <!--            </p>-->
  <!--        </div>-->
  <!--        <div class="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">-->
  <!--            {#each subjects as [code, name]}-->
  <!--                <a href="/stats/{code}" class="flex h-full w-full">-->
  <!--                    <Card class="flex flex-col h-full w-full">-->
  <!--                        <CardHeader>-->
  <!--                            <CardTitle class="truncate">{name}</CardTitle>-->
  <!--                            <CardDescription class="font-bold truncate">{code}</CardDescription>-->
  <!--                        </CardHeader>-->
  <!--                    </Card>-->
  <!--                </a>-->
  <!--            {/each}-->
  <!--        </div>-->
  <!--    </section>-->
  <!--    <section class="text-sm my-8 text-center text-muted-foreground block">-->
  <!--        <span>-->
  <!--            You've got to be bored to scroll all the way here. Here's a cookie.-->
  <!--        </span>-->
  <!--        <Cookie class="inline-block ml-2" />-->
  <!--    </section>-->
</ContentWrapper>
