<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header/index.js";
    import {Button} from "$lib/components/ui/button";
    import Announcement from "$lib/components/announcement.svelte";
    import {Card, CardHeader, CardTitle, CardContent} from "$lib/components/ui/card";
    import { setSearchFilters } from "$lib/searchModalStore";
</script>

<ContentWrapper>
    <PageHeader>
        <Announcement/>
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

    <!-- bento grid showcasing features -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-7xl mx-auto px-4">
        <!-- Card 1: Upload Transcript -->
        <a href="/upload" class="col-span-1 md:col-span-2 lg:col-span-1">
            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">
                <CardHeader>
                    <CardTitle>Upload Transcript</CardTitle>
                </CardHeader>
                <CardContent>
                    Upload your transcript to automatically analyze and visualize your completed courses.
                </CardContent>
            </Card>
        </a>
        <!-- Department Map Card -->
        <a href="/explorer" onclick={() => setSearchFilters(['showDepartments'])} class="col-span-1">
            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">
                <CardHeader>
                    <CardTitle>Display Map of a Department</CardTitle>
                </CardHeader>
                <CardContent>
                    View an interactive map of a department and course relationships to explore course offerings.
                </CardContent>
            </Card>
        </a>
        <!-- Course and Instructor Details Card -->
        <a href="/explorer" onclick={() => setSearchFilters(['showCourses', 'showInstructors'])} class="col-span-1">
            <Card class="w-full h-full hover:shadow-lg hover:scale-105 transition-transform">
                <CardHeader>
                    <CardTitle>Course and Instructor Details</CardTitle>
                </CardHeader>
                <CardContent>
                    Dive into detailed information about individual courses and instructors.
                </CardContent>
            </Card>
        </a>
    </div>
</ContentWrapper>
