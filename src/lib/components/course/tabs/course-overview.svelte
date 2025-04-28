<script lang="ts">
    import {ArrowUpRight, BookA, BookPlus, CircleCheckBig, Users} from "@lucide/svelte";
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import GradeDataHorizontalBarChart from "$lib/components/charts/grade-data-horizontal-bar-chart.svelte";
    import CourseCarousel from "$lib/components/course-carousel/course-carousel.svelte";
    import Change from "$lib/components/change.svelte";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import type {Course} from "$lib/types/course.ts";
    import type {Terms} from "$lib/types/terms.ts";
    import {type FullInstructorInformation} from "$lib/types/instructor.ts";
    import {calculateARate, calculateCompletionRate, calculateGradePointAverage} from "$lib/types/madgrades.ts";

    interface Props {
        course: Course;
        terms: Terms;
        selectedTerm: string | undefined;
        instructors: FullInstructorInformation[];
    }

    let {
        course,
        terms,
        selectedTerm,
        instructors,
    }: Props = $props();

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

    const getLatestTermGPA = (course: Course) => {
        return calculateGradePointAverage(getTermGradeData(course))
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

    const getPercentChange = (latest: number | null, cumulative: number | null) => {
        if (cumulative !== null && latest !== null) {
            return ((latest - cumulative) / cumulative) * 100
        }
        return null
    }

    function getCumulativeGPA(course: Course) {
        return calculateGradePointAverage(course?.cumulative_grade_data)
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

    const getCumulativeCompletionRate = (course: Course) => {
        return calculateCompletionRate(course.cumulative_grade_data)
    }

    const appendPercent = (value: number | null) => {
        if (value === null) {
            return "Not Reported"
        }
        return `${value.toFixed(2)}%`
    }

</script>

<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
    <Card>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-sm font-medium">Grade Point Average</CardTitle>
            <BookPlus class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <div class="text-2xl font-bold {calculateColorFromGPA(getLatestTermGPA(course))}">
                {getLatestTermGPA(course)?.toFixed(2) ?? "Not Reported"}
            </div>
            <Change class="mt-0.5 text-xs"
                    comparisonKeyword="Historical"
                    points={getPercentChange(getLatestTermGPA(course), getCumulativeGPA(course))}/>
        </CardContent>
    </Card>
    <Card>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-sm font-medium">Completion Rate</CardTitle>
            <CircleCheckBig class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <div class="text-2xl font-bold">
                {appendPercent(getLatestCompletionRate(course))}
            </div>
            <Change class="mt-0.5 text-xs"
                    comparisonKeyword="Historical"
                    points={getPercentChange(getLatestCompletionRate(course), getCumulativeCompletionRate(course))}/>
        </CardContent>
    </Card>
    <Card>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-sm font-medium">A Rate</CardTitle>
            <BookA class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <div class="text-2xl font-bold">
                {appendPercent(getLatestARate(course))}
            </div>
            <Change class="mt-0.5 text-xs"
                    comparisonKeyword="Historical"
                    points={getPercentChange(getLatestARate(course), getCumulativeARate(course))}/>
        </CardContent>
    </Card>
    <Card>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-sm font-medium">Class Size</CardTitle>
            <Users class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <div class="text-2xl font-bold">
                {getLatestClassSize(course) ?? "Not Reported"}
            </div>
            <Change class="mt-0.5 text-xs"
                    comparisonKeyword="Historical"
                    points={getPercentChange(getLatestClassSize(course), getCumulativeClassSize(course))}/>
        </CardContent>
    </Card>
</div>
<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
    <Card class="lg:col-span-4">
        <CardContent class="pt-6">
            {#if course.cumulative_grade_data}
                <GradeDataHorizontalBarChart cumulative={course.cumulative_grade_data}
                                             termData={course.term_data}/>
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
            {#each instructors as instructor}
                <InstructorPreview {instructor} showRating={true}/>
            {/each}
        </CardContent>
    </Card>
    <div class="md:col-span-2 lg:col-span-7">
        <h2 class="text-2xl font-bold my-4">Similar Courses</h2>
        <CourseCarousel courseReferences={course.similar_courses ? course.similar_courses : []}/>
    </div>
</div>