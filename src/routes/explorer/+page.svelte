<script lang="ts">

    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header";
    import Search from "$lib/components/search.svelte";
    import {Card, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import {Award, UserPen, Waypoints, Cookie} from "@lucide/svelte";
    import Github from "$lib/components/icons/github.svelte";

    let {data} = $props();

    let {subjects} = $derived(data)

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
            <Search fake={true} wide={true}/>
        </div>
    </PageHeader>
    <section class="my-4">
        <div class="my-8">
            <h2 class="text-4xl font-bold my-2">
                Frequently Visited
            </h2>
            <p class="text-muted-foreground">
                Not sure where to start? Here are some fun and random facts about the courses, instructors, and programs offered by the University of Wisconsin-Madison.
            </p>
        </div>
        <div class="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            <a href="/courses/easiest" class="flex h-full">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle class="flex truncate">
                            <Award class="size-4 mr-2"/>
                            Easiest Courses
                        </CardTitle>
                    </CardHeader>
                    <CardDescription class="px-6">
                        These classes are pretty much guaranteed to get you an A, if you want to take an easy class.
                    </CardDescription>
                </Card>
            </a>
            <a href="/instructors/by-rating-count" class="flex h-full">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle class="flex truncate">
                            <UserPen class="size-4 mr-2"/>
                            Most Rated Instructors
                        </CardTitle>
                    </CardHeader>
                    <CardDescription class="px-6">
                        Who has the most ratings on Rate My Professors, regardless of their rating? We've got the top 100.
                    </CardDescription>
                </Card>
            </a>
            <a href="/explorer/all" class="flex h-full">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle class="flex truncate">
                            <Waypoints class="size-4 mr-2"/>
                            University Graph
                        </CardTitle>
                    </CardHeader>
                    <CardDescription class="px-6">
                        All the prerequisite relations at UW-Madison, visualized.
                        It's computationally expensive, so it may take a while to load.
                    </CardDescription>
                </Card>
            </a>
            <a href="https://github.com/twangodev/uw-coursemap/issues" class="flex h-full">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle class="flex truncate">
                            <Github class="size-4 mr-2"/>
                            Request Another Fact
                        </CardTitle>
                    </CardHeader>
                    <CardDescription class="px-6">
                        Can't get enough? Me neither, but I'm running out of ideas. Request another fun fact or feature on our GitHub repository.
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