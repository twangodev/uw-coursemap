<script lang="ts">
    import {type Course, sanitizeCourseToReferenceString} from "$lib/types/course.js";
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {BookOpen} from "@lucide/svelte";
    import {Button} from "$lib/components/ui/button/index.js";
    import {env} from "$env/dynamic/public";

    const {PUBLIC_API_URL} = env;

    interface Props {
        course: Course;
    }

    let {
        course
    }: Props = $props();
</script>

<Card class="h-[600px] flex flex-col">
    <CardHeader>
        <div class="flex items-center justify-between">
            <div>
                <CardTitle>Course Prerequisites Map</CardTitle>
                <CardDescription>
                    Visual representation of course prerequisites and related courses
                </CardDescription>
            </div>
            <Button
                    class="flex items-center gap-2"
                    href="/explorer/{course.course_reference.subjects[0]}?focus={sanitizeCourseToReferenceString(course.course_reference)}"
                    size="sm"
                    variant="outline"
            >
                <BookOpen class="h-4 w-4"/>
                View on Department Graph
            </Button>
        </div>
    </CardHeader>
    <CardContent class="flex-1">
        <div class="flex h-full w-full">
            <Cytoscape
                    filter={course}
                    styleUrl="{PUBLIC_API_URL}/styles/{course.course_reference.subjects[0]}.json"
                    url="{PUBLIC_API_URL}/graphs/course/{sanitizeCourseToReferenceString(course.course_reference)}.json"
            />
        </div>
    </CardContent>
</Card>