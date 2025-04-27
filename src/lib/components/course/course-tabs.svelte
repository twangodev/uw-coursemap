<script lang="ts">
    import type {Course} from "$lib/types/course.js";
    import {sanitizeCourseToReferenceString} from "$lib/types/course.js";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import {ArrowUpRight, BookOpen} from "lucide-svelte";
    import {Tabs, TabsContent, TabsList, TabsTrigger} from "$lib/components/ui/tabs/index.js";
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {Button} from "$lib/components/ui/button/index.js";
    import {env} from "$env/dynamic/public";
    import type {Terms} from "$lib/types/terms.js";
    import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";
    import CourseDetails from "./course-details.svelte";
    import {CourseOverview} from "$lib/components/course/tabs";
    import {CourseTrends} from "$lib/components/course/tabs/index.js";

    const {PUBLIC_API_URL} = env;

    interface Props {
        course: Course;
        terms: Terms;
        selectedTerm: string | undefined;
    }

    let {
        course,
        terms,
        selectedTerm = $bindable()
    }: Props = $props();

    let instructors: Promise<FullInstructorInformation[]> = $derived(getFullInstructorInformation(course, terms, selectedTerm))

</script>

<Tabs value="overview">
    <TabsList class="my-2">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="trends">Trends</TabsTrigger>
        <TabsTrigger value="instructors">Instructors</TabsTrigger>
        <TabsTrigger value="prerequisites">Prerequisites Map</TabsTrigger>
    </TabsList>
    <div class="grid gap-4 lg:grid-cols-12">
        <CourseDetails {course} {selectedTerm}/>
        <TabsContent class="lg:col-span-9 space-y-4" value="overview">
            <CourseOverview {course} {selectedTerm} {terms}/>
        </TabsContent>
        <TabsContent class="lg:col-span-9 space-y-4" value="trends">
            <CourseTrends {course} {terms}/>
        </TabsContent>
        <TabsContent class="lg:col-span-9 space-y-4" value="instructors">
            <Card>
                <CardHeader>
                    <CardTitle>Instructors</CardTitle>
                    <CardDescription class="flex">
                        Sorted by ratings from
                        <a class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
                           href="https://www.ratemyprofessors.com/"
                           target="_blank"
                        >
                            Rate My Professors
                            <ArrowUpRight class="h-4 w-4 inline"/>
                        </a>
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {#await instructors}
                        <p class="text-center">Loading...</p>
                    {:then instructors}
                        {#each instructors as instructor}
                            <InstructorPreview
                                    {instructor}
                                    showRating={true}
                                    showOtherDetails={true}
                            />
                        {/each}
                    {:catch error}
                        <p class="text-red-600">Error loading instructors: {error.message}</p>
                    {/await}
                </CardContent>
            </Card>
            <Card>
                {#await instructors}
                    <p class="text-center">Loading...</p>
                {:then instructors}
                    <CardContent>
                        <InstructorWordCloud instructors={instructors}/>
                    </CardContent>
                {:catch error}
                    <p class="text-red-600">Error loading instructors: {error.message}</p>
                {/await}
            </Card>
        </TabsContent>
        <TabsContent class="lg:col-span-9 space-y-4" value="prerequisites">
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
        </TabsContent>
    </div>
</Tabs>