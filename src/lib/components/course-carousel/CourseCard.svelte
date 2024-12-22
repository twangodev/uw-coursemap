<script lang="ts">

    import {type Course, courseReferenceToString, sanitizeCourseToReferenceString} from "$lib/types/course.ts";
    import {Card, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";

    export let course: Course

</script>

<a href="/course/{sanitizeCourseToReferenceString(course.course_reference)}" target="_parent"> <!-- TODO fix reactivity on +page.svelte for courseIdentifier slug -->
    <Card class="w-full max-w-64 overflow-hidden">
        <CardHeader class="pb-0">
            <CardTitle class="truncate">{course.course_title}</CardTitle>
            <CardDescription class="font-bold truncate">{courseReferenceToString(course.course_reference)}</CardDescription>
            <CardDescription class="line-clamp-4">{course.description}</CardDescription>
        </CardHeader>
    </Card>
</a>
