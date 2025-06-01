<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header/index.js";
    import {Button} from "$lib/components/ui/button";
    import Announcement from "$lib/components/announcement.svelte";
    import RotatingTiltCard from "$lib/components/rotating-tilt-card.svelte";
    import QuickStatistics from "$lib/components/quick-statistics.svelte";
    import CallToAction from "$lib/components/call-to-action.svelte";
</script>

<div class="w-full">
    <ContentWrapper class="w-full">
        <div class="z-2 absolute inset-0 isolate hidden opacity-50 contain-strict lg:block">
            <div class="w-140 h-320 -translate-y-87.5 absolute left-0 top-0 -rotate-45 rounded-full bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,hsla(0,0%,85%,.08)_0,hsla(0,0%,55%,.02)_50%,hsla(0,0%,45%,0)_80%)]"></div>
            <div class="h-320 absolute left-0 top-0 w-60 -rotate-45 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.06)_0,hsla(0,0%,45%,.02)_80%,transparent_100%)] [translate:5%_-50%]"></div>
            <div class="h-320 -translate-y-87.5 absolute left-0 top-0 w-60 -rotate-45 bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.04)_0,hsla(0,0%,45%,.02)_80%,transparent_100%)]"></div>
        </div>
        <section class="bg-white dark:bg-transparent">
            <div class="relative mx-auto max-w-5xl px-6 py-28 lg:py-24">
                <div class="relative z-10 mx-auto text-center">
                    <Announcement/>
                    <PageHeaderHeading>
                        Course exploration, made easy
                    </PageHeaderHeading>
                    <PageHeaderDescription>
                        Explore the courses offered by the UW-Madison in a visual and interactive way.
                    </PageHeaderDescription>
                    <p class="text-center text-sm text-primary mt-3">
                        UW Course Map is not affiliated with the University of Wisconsin-Madison.
                    </p>
                    <div class="py-4 md:pb-10">
                        <Button href="/explorer">
                            Get Started
                        </Button>
                    </div>
                </div>
            </div>

        </section>
    </ContentWrapper>

    <RotatingTiltCard/>

    <ContentWrapper>
        <QuickStatistics/>
        <CallToAction />
    </ContentWrapper>

</div>

<!--<ContentWrapper>-->
<!--    <PageHeader>-->
<!--        <Announcement/>-->
<!--        <PageHeaderHeading>Course exploration, made easy</PageHeaderHeading>-->
<!--        <PageHeaderDescription class="text-muted-foreground">-->
<!--            Explore the courses offered by the UW-Madison in a visual and interactive way.-->
<!--        </PageHeaderDescription>-->
<!--        <p class="text-center text-sm text-primary">-->
<!--            UW Course Map is not affiliated by the University of Wisconsin-Madison.-->
<!--        </p>-->

<!--        <div class="flex w-full items-center justify-center space-x-4 py-4 md:pb-10">-->
<!--            <Button href="/explorer">-->
<!--                Get Started-->
<!--            </Button>-->
<!--        </div>-->
<!--    </PageHeader>-->

<!--    &lt;!&ndash; bento grid showcasing features &ndash;&gt;-->
<!--    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-7xl mx-auto px-4">-->
<!--        &lt;!&ndash; Card 1: Upload Transcript &ndash;&gt;-->
<!--        <a href="/upload" class="col-span-1 md:col-span-2 lg:col-span-1">-->
<!--            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">-->
<!--                <CardHeader>-->
<!--                    <CardTitle>Upload Transcript</CardTitle>-->
<!--                </CardHeader>-->
<!--                <CardContent>-->
<!--                    Upload your transcript to automatically analyze and visualize your completed courses.-->
<!--                </CardContent>-->
<!--            </Card>-->
<!--        </a>-->
<!--        &lt;!&ndash; Department Map Card &ndash;&gt;-->
<!--        <a href="/explorer" onclick={() => setSearchFilters(['showDepartments'])} class="col-span-1">-->
<!--            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">-->
<!--                <CardHeader>-->
<!--                    <CardTitle>Display Map of a Department</CardTitle>-->
<!--                </CardHeader>-->
<!--                <CardContent>-->
<!--            </Card>-->
<!--        </a>-->
<!--        &lt;!&ndash; Course and Instructor Details Card &ndash;&gt;-->
<!--        <a href="/explorer" onclick={() => setSearchFilters(['showCourses', 'showInstructors'])} class="col-span-1">-->
<!--            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">-->
<!--                <CardHeader>-->
<!--                    <CardTitle>Course and Instructor Details</CardTitle>-->
<!--                </CardHeader>-->
<!--                <CardContent>-->
<!--                    Dive into detailed information about individual courses and instructors.-->
<!--                </CardContent>-->
<!--            </Card>-->
<!--        </a>-->
<!--    </div>-->
<!--</ContentWrapper>-->
