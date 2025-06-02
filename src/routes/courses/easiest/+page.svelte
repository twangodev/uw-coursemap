<script lang="ts">

    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header";
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {courseReferenceToString, sanitizeCourseToReferenceString} from "$lib/types/course.ts";
    import {Card, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card";
    import {Badge} from "$lib/components/ui/badge/index.js";

    let { data } = $props();

    let { courses } = $derived(data)

</script>

<ContentWrapper>
    <PageHeader>
        <PageHeaderHeading>Easiest Courses</PageHeaderHeading>
        <PageHeaderDescription class="text-muted-foreground">
            These classes are pretty much guaranteed to get you an A, if you want to take an easy class.
        </PageHeaderDescription>
    </PageHeader>

    <div class="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {#each courses as course, index}
            <a href="/courses/{sanitizeCourseToReferenceString(course.course_reference)}" target="_blank" class="flex h-full w-full">
                <Card class="w-full my-4 overflow-hidden">
                    <CardHeader class="pb-0">
                        <CardTitle class="flex flex-row items-center justify-between space-y-0">
                            <span class="truncate">{course.course_title}</span>
                            <Badge variant="outline" class="text-muted-foreground">#{index + 1}</Badge>
                        </CardTitle>
                        <CardDescription class="font-bold truncate">{courseReferenceToString(course.course_reference)}</CardDescription>
                        <CardDescription class="line-clamp-4">{course.description}</CardDescription>
                    </CardHeader>
                </Card>
            </a>
        {/each}
    </div>

</ContentWrapper>
