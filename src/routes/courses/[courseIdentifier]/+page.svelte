<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {page} from '$app/state';
    import ContentH1 from "$lib/components/content/content-h1.svelte";
    import {type Course, courseReferenceStringToCourse} from "$lib/types/course.ts";
    import {courseReferenceToString} from "$lib/types/course.js";
    import {
        ArrowUpRight,
        BookA,
        BookOpen,
        BookPlus,
        CalendarRange,
        CircleCheckBig,
        ClipboardCheck,
        Info,
        Users
    } from "lucide-svelte";
    import {calculateARate, calculateCompletionRate, calculateGradePointAverage} from "$lib/types/madgrades.ts";
    import Change from "$lib/components/change.svelte";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";
    import GradeDataHorizontalBarChart from "$lib/components/charts/grade-data-horizontal-bar-chart.svelte";
    import CourseCarousel from "$lib/components/course-carousel/course-carousel.svelte";
    import ComboGradeDataStackedAreaChart from "$lib/components/charts/combo-grade-data-stacked-area-chart.svelte";
    import {apiFetch} from "$lib/api.ts";
    import {getLatestTermIdPromise, type Terms} from "$lib/types/terms.ts";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
    import TermSelector from "$lib/components/term-selector.svelte";
    import {Tabs, TabsContent, TabsList, TabsTrigger} from "$lib/components/ui/tabs";
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card";

    let courseIdentifier = $derived(page.params.courseIdentifier);

    let course: Promise<Course> = $derived(courseReferenceStringToCourse(courseIdentifier));

    let terms: Promise<Terms> = (async () => {
        let termsData = await apiFetch(`/terms.json`)
        return await termsData.json()
    })();

    let selectedTerm: string | undefined = $state(undefined)
    let instructors: Promise<FullInstructorInformation[]> = $derived(getFullInstructorInformation(course, terms, selectedTerm))

    let latestTerm = $derived.by(async () => {
        selectedTerm = String(await getLatestTermIdPromise(terms))
        return selectedTerm
    });

    let currentCourseIdentifier: string | null = null;

    function termsWithEnrollmentData(course: Course) {
        const allTerms = Object.keys(course?.term_data ?? {}).sort((a, b) => Number(a) - Number(b));
        return allTerms.filter(term => course.term_data[term]?.enrollment_data != null);
    }

    function getLatestEnrollmentData(course: Course) {
        const validTerms = termsWithEnrollmentData(course);
        if (!validTerms.length) return null;
        const latestTerm = validTerms[validTerms.length - 1];

        let candidateTerm = selectedTerm ?? latestTerm;
        return course.term_data[candidateTerm]?.enrollment_data ?? course.term_data[latestTerm].enrollment_data;
    }
    
    function termsWithGradeData(course: Course) {
        const allTerms = Object.keys(course?.term_data ?? {}).sort((a, b) => Number(a) - Number(b));
        return allTerms.filter(term => course.term_data[term]?.grade_data != null);
    }

    function getTermGradeData(course: Course) {
        const validTerms = termsWithGradeData(course);
        if (!validTerms.length) return null;
        const latestTerm = validTerms[validTerms.length - 1];

        let candidateTerm = selectedTerm ?? latestTerm;
        return course.term_data[candidateTerm]?.grade_data ?? course.term_data[latestTerm].grade_data;
    }

    function getCumulativeGPA(course: Course) {
        return calculateGradePointAverage(course?.cumulative_grade_data)
    }

    const getLatestTermGPA = (course: Course) => {
        return calculateGradePointAverage(getTermGradeData(course))
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
        return calculateCompletionRate(course.cumulative_grade_data)
    }

    const getLatestCompletionRate = (course: Course) => {
        return calculateCompletionRate(getTermGradeData(course))
    }

    const getCumulativeARate = (course: Course) => {
        return calculateARate(course.cumulative_grade_data)
    }

    const getLatestARate = (course: Course) => {
        return calculateARate(getTermGradeData(course))
    }

    const getCumulativeClassSize = (course: Course) => {
        return (course.cumulative_grade_data?.total ?? 0) / termsWithGradeData(course).length;
    }

    const getLatestClassSize = (course: Course) => {
        return getTermGradeData(course)?.total ?? 0
    }

    const appendPercent = (value: number | null) => {
        if (value === null) {
            return "Not Reported"
        }
        return `${value.toFixed(2)}%`
    }

    const getCreditCount = (course: Course) => {
        const creditCount = getLatestEnrollmentData(course)?.credit_count;
        if (!creditCount) {
            return "Not Reported";
        }

        if (creditCount[0] === creditCount[1]) {
            return `${creditCount[0]}`;
        } else {
            return `${creditCount[0]} to ${creditCount[1]}`;
        }
    }

    const getNormallyOffered = (course: Course) => {
        return getLatestEnrollmentData(course)?.typically_offered ?? "Not Reported";
    }

</script>

<ContentWrapper>
    {#await Promise.all([course, terms, latestTerm])}
        <p class="text-center">Loading...</p>
    {:then [course, terms]}
        <div class="flex justify-between items-center">
            <div>
                <ContentH1>{course.course_title}</ContentH1>
                <div class="text-xl font-bold my-2">
                    {courseReferenceToString(course.course_reference)}
                </div>
            </div>
            <TermSelector bind:selectedTerm={selectedTerm} terms={terms} />
        </div>
        <Tabs value="overview">
            <TabsList class="my-2">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="trends">Trends</TabsTrigger>
                <TabsTrigger value="instructors">Instructors</TabsTrigger>
            </TabsList>
            <div class="grid gap-4 lg:grid-cols-12">
                <div class="space-y-4 mt-2 lg:col-span-3">
                    <Card>
                        <CardHeader
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <CardTitle class="text-base font-medium">Course Description</CardTitle>
                            <Info class="text-muted-foreground h-4 w-4" />
                        </CardHeader>
                        <CardContent>
                            <p class="text-sm break-words">{course.description}</p>
                        </CardContent>
                        <CardHeader
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <CardTitle class="text-base font-medium">Prerequisties</CardTitle>
                            <BookOpen class="text-muted-foreground h-4 w-4" />
                        </CardHeader>
                        <CardContent>
                            <p class="text-sm break-words">{course.prerequisites.prerequisites_text}</p>
                        </CardContent>
                        <div class="flex flex-row space-x-4">
                            <div class="flex-1">
                                <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle class="text-base font-medium">Credits</CardTitle>
                                    <ClipboardCheck class="text-muted-foreground h-4 w-4" />
                                </CardHeader>
                                <CardContent>
                                    <p class="text-sm break-words">{getCreditCount(course)}</p>
                                </CardContent>
                            </div>
                            <div class="flex-1">
                                <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle class="text-base font-medium">Offered</CardTitle>
                                    <CalendarRange class="text-muted-foreground h-4 w-4" />
                                </CardHeader>
                                <CardContent>
                                    <p class="text-sm break-words">{getNormallyOffered(course)}</p>
                                </CardContent>
                            </div>
                        </div>
                    </Card>
                </div>
                <TabsContent value="overview" class="lg:col-span-9 space-y-4">
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Grade Point Average</CardTitle>
                                <BookPlus class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold {calculateColorFromGPA(getLatestTermGPA(course))}">
                                    {getLatestTermGPA(course)?.toFixed(2) ?? "Not Reported"}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestTermGPA(course), getCumulativeGPA(course))} comparisonKeyword="Historical"/>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Completion Rate</CardTitle>
                                <CircleCheckBig class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold">
                                    {appendPercent(getLatestCompletionRate(course))}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestCompletionRate(course), getCumulativeCompletionRate(course))} comparisonKeyword="Historical"/>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">A Rate</CardTitle>
                                <BookA class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold">
                                    {appendPercent(getLatestARate(course))}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestARate(course), getCumulativeARate(course))} comparisonKeyword="Historical"/>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Class Size</CardTitle>
                                <Users class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold">
                                    {getLatestClassSize(course) ?? "Not Reported"}
                                </div>
                                <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestClassSize(course), getCumulativeClassSize(course))} comparisonKeyword="Historical"/>
                            </CardContent>
                        </Card>
                    </div>
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                        <Card class="lg:col-span-4">
                            <CardContent class="pt-6">
                                {#if course.cumulative_grade_data}
                                    <GradeDataHorizontalBarChart cumulative={course.cumulative_grade_data} termData={course.term_data} />
                                {:else}
                                    <p class="text-center">No data available</p>
                                {/if}
                            </CardContent>
                        </Card>
                        <Card class="lg:col-span-3">
                            <CardHeader>
                                <CardTitle>Instructors ({selectedTerm ? terms[selectedTerm] : ""})</CardTitle>
                                <CardDescription class="flex">
                                    Sorted by ratings from
                                    <a href="https://www.ratemyprofessors.com/"
                                       class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
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
                                        <InstructorPreview {instructor} showRating={true} />
                                    {/each}
                                {:catch error}
                                    <p class="text-red-600">Error loading instructors: {error.message}</p>
                                {/await}
                            </CardContent>
                        </Card>
                        <div class="md:col-span-2 lg:col-span-7">
                            <h2 class="text-2xl font-bold my-4">Similar Courses</h2>
                            <CourseCarousel courseReferences={course.similar_courses}/>
                        </div>
                    </div>
                </TabsContent>
                <TabsContent value="trends" class="lg:col-span-9 space-y-4">
                    <Card>
                        <CardContent class="pt-6">
                            {#if course.cumulative_grade_data}
                                <ComboGradeDataStackedAreaChart term_data={course.term_data} {terms} />
                            {:else }
                                <p class="text-center">No data available</p>
                            {/if}
                        </CardContent>
                    </Card>
                </TabsContent>
                <TabsContent value="instructors" class="lg:col-span-9 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Instructors</CardTitle>
                            <CardDescription class="flex">
                                Sorted by ratings from
                                <a href="https://www.ratemyprofessors.com/"
                                   class="ml-1 flex items-center font-medium hover:underline underline-offset-4"
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
                                <InstructorWordCloud instructors={instructors} />
                            </CardContent>
                        {:catch error}
                            <p class="text-red-600">Error loading instructors: {error.message}</p>
                        {/await}
                    </Card>
                </TabsContent>
            </div>
        </Tabs>
    {:catch error}
        <p class="text-red-600">Error loading course: {error.message}</p>
    {/await}
</ContentWrapper>