<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {PageHeader, PageHeaderDescription, PageHeaderHeading} from "$lib/components/page-header/index.js";
    import {Button} from "$lib/components/ui/button";
    import Announcement from "$lib/components/announcement.svelte";
    import {Card, CardHeader, CardTitle, CardContent} from "$lib/components/ui/card";
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
    </PageHeader>

    <!-- Flex container for feature cards -->
    <div class="flex flex-wrap justify-center gap-6">
        <!-- Card 1: Upload Transcript -->
        <a href="/upload" class="w-80">
            <Card class="w-full hover:shadow-lg hover:scale-105 transition-transform">
                <CardHeader>
                    <CardTitle>Upload Transcript</CardTitle>
                </CardHeader>
                <CardContent>
                    Upload your transcript to automatically analyze and visualize your completed courses.
                </CardContent>
            </Card>
        </a>
        <a href="/explorer" class="w-80">
            <Card class="w-80 hover:shadow-lg hover:scale-105 transition-transform">
            <CardHeader>
                <CardTitle>Display Map of Departments</CardTitle>
            </CardHeader>
            <CardContent>
                View an interactive map of departments and their relationships to explore course offerings.
            </CardContent>
            </Card>
        </a>
        <!-- Card 2: Display Graph of Departments -->
        <a href="/explorer">
            <Card class="w-80 hover:shadow-lg hover:scale-105 transition-transform">
                <CardHeader>
                    <CardTitle>Course Details</CardTitle>
                </CardHeader>
                <CardContent>
                    Dive into detailed information about individual courses, including prerequisites and instructors.
                </CardContent>
            </Card>
        </a>        

        <!-- Card 3: Course Details -->
    </div>
</ContentWrapper>
