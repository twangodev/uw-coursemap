<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header/index.js";
  import { Button } from "$lib/components/ui/button";
  import Announcement from "$lib/components/announcement.svelte";
  import RotatingTiltCard from "$lib/components/rotating-tilt-card.svelte";
  import QuickStatistics from "$lib/components/quick-statistics.svelte";
  import CallToAction from "$lib/components/call-to-action.svelte";
  import { inView } from "$lib/actions/in-view";
  import { m } from "$lib/paraglide/messages";
</script>

<div class="w-full">
  <ContentWrapper class="w-full">
    <div
      class="absolute inset-0 isolate z-2 hidden opacity-50 contain-strict lg:block"
    >
      <div
        class="absolute top-0 left-0 h-320 w-140 -translate-y-87.5 -rotate-45 rounded-full bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,hsla(0,0%,85%,.08)_0,hsla(0,0%,55%,.02)_50%,hsla(0,0%,45%,0)_80%)]"
      ></div>
      <div
        class="absolute top-0 left-0 h-320 w-60 [translate:5%_-50%] -rotate-45 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.06)_0,hsla(0,0%,45%,.02)_80%,transparent_100%)]"
      ></div>
      <div
        class="absolute top-0 left-0 h-320 w-60 -translate-y-87.5 -rotate-45 bg-[radial-gradient(50%_50%_at_50%_50%,hsla(0,0%,85%,.04)_0,hsla(0,0%,45%,.02)_80%,transparent_100%)]"
      ></div>
    </div>
    <section class="bg-white dark:bg-transparent">
      <div class="relative mx-auto max-w-5xl px-6 py-28 lg:py-24">
        <div class="relative z-10 mx-auto text-center">
          <Announcement />
          <PageHeaderHeading>{m["home.hero.title"]()}</PageHeaderHeading>
          <PageHeaderDescription>
            {m["home.hero.description"]()}
          </PageHeaderDescription>
          <p class="text-primary mt-3 text-center text-sm">
            {m["home.hero.disclaimer"]()}
          </p>
          <div class="py-4 md:pb-10">
            <Button href="/explorer" class="animate-fade-in [animation-delay:100ms] [animation-fill-mode:both]">{m["home.hero.getStarted"]()}</Button>
          </div>
        </div>
      </div>
    </section>
  </ContentWrapper>

  <RotatingTiltCard />

  <ContentWrapper>
    <div use:inView={{ threshold: 0.3 }} class="opacity-0 translate-y-10 transition-all duration-800 [&.in-view]:opacity-100 [&.in-view]:translate-y-0">
      <QuickStatistics />
    </div>
    <div use:inView={{ threshold: 0.5 }} class="opacity-0 scale-95 transition-all duration-600 [&.in-view]:opacity-100 [&.in-view]:scale-100">
      <CallToAction />
    </div>
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
