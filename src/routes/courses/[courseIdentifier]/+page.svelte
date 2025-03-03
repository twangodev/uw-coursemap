<script lang="ts">
    import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import { page } from '$app/stores';
    import ContentH1 from "$lib/components/content/ContentH1.svelte";
    import {onMount} from "svelte";
    import {writable} from "svelte/store";
    import {type Course, courseReferenceStringToCourse} from "$lib/types/course.ts";
    import {courseReferenceToString} from "$lib/types/course.js";
    import * as Tabs from "$lib/components/ui/tabs";
    import * as Card from "$lib/components/ui/card";
    import {
        BookA,
        BookOpen,
        BookPlus, CircleCheckBig,
        Info,
        Users,
        ArrowUpRight
    } from "lucide-svelte";
    import {ScrollArea} from "$lib/components/ui/scroll-area";
    import {calculateARate, calculateCompletionRate, calculateGradePointAverage} from "$lib/types/madgrades.ts";
    import Change from "$lib/components/Change.svelte";
    import InstructorPreview from "$lib/components/instructor-preview/InstructorPreview.svelte";
    import type {FullInstructorInformation, Instructor} from "$lib/types/instructor.ts";
    import GradeDataHorizontalBarChart from "$lib/components/charts/GradeDataHorizontalBarChart.svelte";
    import CourseCarousel from "$lib/components/course-carousel/CourseCarousel.svelte";
    import GradeDataStackedAreaChart from "$lib/components/charts/ComboGradeDataStackedAreaChart.svelte";
    import {apiFetch} from "$lib/api.ts";
    import type {Terms} from "$lib/types/terms.ts";
    import InstructorWordCloud from "$lib/components/charts/InstructorWordCloud.svelte";

    $: courseIdentifier = $page.params.courseIdentifier;

    let course = writable<Course | null>(null)
    let instructors: FullInstructorInformation[] = []

    const getLatestTermMadgradesData = (course: Course) => {
        let allTerms = Object.keys(course?.madgrades_data?.by_term ?? {}).sort()
        let latestTerm = allTerms[allTerms.length - 1]
        return course?.madgrades_data?.by_term[latestTerm] ?? null
    }

    const getCumulativeGPA = (course: Course) => {
        return calculateGradePointAverage(course?.madgrades_data?.cumulative)
    }

    const getLatestTermGPA = (course: Course) => {
        return calculateGradePointAverage(getLatestTermMadgradesData(course))
    }

    const getPercentChange = (latest: number | null, cumulative: number | null) => {
        if (cumulative !== null && latest !== null) {
            return ((latest - cumulative) / cumulative) * 100
        }
        return null
    }

    const calculateColorFromGPA = (gpa: number | null) => {
        if (gpa === null) {
            return ""
        }
        if (gpa >= 3.5) {
            return "text-green-600 dark:text-green-400"
        } else if (gpa >= 3.0) {
            return "text-amber-600 dark:text-yellow-400"
        } else if (gpa >= 2.5) {
            return "text-orange-600 dark:text-orange-400"
        } else {
            return "text-red-600 dark:text-red-400"
        }
    }

    const getCumulativeCompletionRate = (course: Course) => {
        return calculateCompletionRate(course.madgrades_data?.cumulative)
    }

    const getLatestCompletionRate = (course: Course) => {
        return calculateCompletionRate(getLatestTermMadgradesData(course))
    }

    const getCumulativeARate = (course: Course) => {
        return calculateARate(course.madgrades_data?.cumulative)
    }

    const getLatestARate = (course: Course) => {
        return calculateARate(getLatestTermMadgradesData(course))
    }

    const getCumulativeClassSize = (course: Course) => {
        let average = 0;
        if (!course?.madgrades_data?.by_term) {
            return 0
        }
        for (let term in course.madgrades_data.by_term) {
            average += course.madgrades_data.by_term[term].total
        }
        return average / Object.keys(course.madgrades_data.by_term).length
    }

    const getLatestClassSize = (course: Course) => {
        return getLatestTermMadgradesData(course)?.total ?? 0
    }

    const appendPercent = (value: number | null) => {
        if (value === null) {
            return "Not Reported"
        }
        return `${value.toFixed(2)}%`
    }

    let terms: Terms

    onMount(async () => {
        let termsData = await apiFetch(`/terms.json`)
        terms = await termsData.json()

        let courseData = await courseReferenceStringToCourse(courseIdentifier)
        $course = courseData

        for (let [name, email] of Object.entries(courseData?.enrollment_data?.instructors ?? {})) {
            let response = await apiFetch(`/instructors/${name.replaceAll(' ', '_').replaceAll('/', '_')}.json`)
            let data: FullInstructorInformation  = response.status == 200 ? await response.json() : {
                name: name,
                email: email,
                credentials: null,
                department: null,
                official_name: null,
                position: null,
                rmp_data: null,
            }

            instructors.push(data)
        }

        instructors = instructors.toSorted((a, b) => {
            if (!a.rmp_data?.average_rating) {
                return 1
            }
            if (!b.rmp_data?.average_rating) {
                return -1
            }
            return b.rmp_data.average_rating - a.rmp_data.average_rating
        })
    })
</script>

<ContentWrapper>
    {#if $course}
        <ContentH1>{$course.course_title}</ContentH1>
        <div class="text-xl font-bold my-2">
            {courseReferenceToString($course.course_reference)}
        </div>
        <Tabs.Root value="overview">
            <Tabs.List class="my-2">
                <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
                <Tabs.Trigger value="trends">Trends</Tabs.Trigger>
                <Tabs.Trigger value="instructors">Instructors</Tabs.Trigger>
            </Tabs.List>
            <div class="grid gap-4 lg:grid-cols-12">
                <div class="space-y-4 mt-2 lg:col-span-3">
                    <Card.Root>
                        <Card.Header
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <Card.Title class="text-base font-medium">Course Description</Card.Title>
                            <Info class="text-muted-foreground h-4 w-4" />
                        </Card.Header>
                        <Card.Content>
                            <p class="text-sm break-words">{$course.description}</p>
                        </Card.Content>
                        <Card.Header
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <Card.Title class="text-base font-medium">Prerequisties</Card.Title>
                            <BookOpen class="text-muted-foreground h-4 w-4" />
                        </Card.Header>
                        <Card.Content>
                            <p class="text-sm break-words">{$course.prerequisites.prerequisites_text}</p>
                        </Card.Content>
                    </Card.Root>
                </div>
                <Tabs.Content value="overview" class="lg:col-span-9 space-y-4">
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <Card.Root>
                            <Card.Header
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <Card.Title class="text-sm font-medium">Grade Point Average</Card.Title>
                                <BookPlus class="text-muted-foreground h-4 w-4" />
                            </Card.Header>
                            <Card.Content>
                                <div class="text-2xl font-bold {calculateColorFromGPA(getLatestTermGPA($course))}">
                                    {getLatestTermGPA($course)?.toFixed(2) ?? "Not Reported"}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestTermGPA($course), getCumulativeGPA($course))} comparisonKeyword="Historical"/>
                            </Card.Content>
                        </Card.Root>
                        <Card.Root>
                            <Card.Header
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <Card.Title class="text-sm font-medium">Completion Rate</Card.Title>
                                <CircleCheckBig class="text-muted-foreground h-4 w-4" />
                            </Card.Header>
                            <Card.Content>
                                <div class="text-2xl font-bold">
                                    {appendPercent(getLatestCompletionRate($course))}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestCompletionRate($course), getCumulativeCompletionRate($course))} comparisonKeyword="Historical"/>
                            </Card.Content>
                        </Card.Root>
                        <Card.Root>
                            <Card.Header
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <Card.Title class="text-sm font-medium">A Rate</Card.Title>
                                <BookA class="text-muted-foreground h-4 w-4" />
                            </Card.Header>
                            <Card.Content>
                                <div class="text-2xl font-bold">
                                    {appendPercent(getLatestARate($course))}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestARate($course), getCumulativeARate($course))} comparisonKeyword="Historical"/>
                            </Card.Content>
                        </Card.Root>
                        <Card.Root>
                            <Card.Header
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <Card.Title class="text-sm font-medium">Class Size</Card.Title>
                                <Users class="text-muted-foreground h-4 w-4" />
                            </Card.Header>
                            <Card.Content>
                                <div class="text-2xl font-bold">
                                    {getLatestClassSize($course) ?? "Not Reported"}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestClassSize($course), getCumulativeClassSize($course))} comparisonKeyword="Historical"/>
                            </Card.Content>
                        </Card.Root>
                    </div>
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                        <Card.Root class="lg:col-span-4">
                            <Card.Content class="pt-6">
                                {#if $course.madgrades_data}
                                    <GradeDataHorizontalBarChart madgradesData={$course.madgrades_data} />
                                {:else}
                                    <p class="text-center">No data available</p>
                                {/if}
                            </Card.Content>
                        </Card.Root>
                        <Card.Root class="lg:col-span-3">
                            <Card.Header>
                                <Card.Title>Instructors</Card.Title>
                                <Card.Description class="flex">
                                    Sorted by ratings from
                                    <a href="https://www.ratemyprofessors.com/"
                                       class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
                                       target="_blank"
                                    >
                                        Rate My Professors
                                        <ArrowUpRight class="h-4 w-4 inline"/>
                                    </a>
                                </Card.Description>
                            </Card.Header>
                            <Card.Content>
                                {#each instructors as instructor}
                                    <InstructorPreview {instructor} showRating={true} />
                                {/each}
                            </Card.Content>
                        </Card.Root>
                        <div class="md:col-span-2 lg:col-span-7">
                            <h2 class="text-2xl font-bold my-4">Related Courses</h2>
                            <CourseCarousel courseReferences={$course.prerequisites.course_references}/>
                        </div>
                    </div>
                </Tabs.Content>
                <Tabs.Content value="trends" class="lg:col-span-9 space-y-4">
                    <Card.Root>
                        <Card.Content class="pt-6">
                            {#if $course.madgrades_data}
                            <GradeDataStackedAreaChart madgradesData={$course.madgrades_data} {terms} />
                            {:else }
                                <p class="text-center">No data available</p>
                            {/if}
                        </Card.Content>
                    </Card.Root>
                </Tabs.Content>
                <Tabs.Content value="instructors" class="lg:col-span-9 space-y-4">
                    <Card.Root>
                        <Card.Header>
                            <Card.Title>Instructors</Card.Title>
                            <Card.Description class="flex">
                                Sorted by ratings from
                                <a href="https://www.ratemyprofessors.com/"
                                   class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
                                   target="_blank"
                                >
                                    Rate My Professors
                                    <ArrowUpRight class="h-4 w-4 inline"/>
                                </a>
                            </Card.Description>
                        </Card.Header>
                        <Card.Content>
                            {#each instructors as instructor}
                                <InstructorPreview
                                    {instructor}
                                    showRating={true}
                                    showOtherDetails={true}
                                />
                            {/each}
                        </Card.Content>
                    </Card.Root>
                    <Card.Root>
                        <Card.Content>
                            <InstructorWordCloud instructors={instructors} />
                        </Card.Content>
                    </Card.Root>
                </Tabs.Content>
            </div>
        </Tabs.Root>
    {/if}
</ContentWrapper>