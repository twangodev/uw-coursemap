<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import { page } from '$app/state';
    import {type Writable, writable} from "svelte/store";
    import {type FullInstructorInformation, getAttendanceRequirement, type Instructor} from "$lib/types/instructor.ts";
    import {apiFetch} from "$lib/api.ts";
    import {
        BookA,
        BookPlus,
        BriefcaseBusiness,
        CircleCheckBig,
        GraduationCap, Mail, PencilRuler, Repeat, Star,
        University,
        Users
    } from "lucide-svelte";
    import {Card, CardContent, CardHeader} from "$lib/components/ui/card";
    import {CardDescription, CardTitle} from "$lib/components/ui/card/index.js";
    import {Avatar, AvatarFallback} from "$lib/components/ui/avatar";
    import RatingDonutChart from "$lib/components/charts/rating-donut-chart.svelte";
    import AttendanceDonutChart from "$lib/components/charts/attendance-donut-chart.svelte";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";

    async function fetchInstructor(name: string) {
        const response = await apiFetch(`/instructors/${name}.json`)
        const data: FullInstructorInformation = await response.json()
        instructor.set(data)
    }

    let instructor: Writable<FullInstructorInformation | null> = writable(null)
    let instructorName = $derived($instructor?.name)
    let attendanceRequirement = $derived(getAttendanceRequirement($instructor?.rmp_data?.mandatory_attendance))

    const calculateRatingColor = (rating: number | undefined) => {
        if (!rating) {
            return "";
        }
        if (rating >= 4) {
            return "text-green-600 dark:text-green-400";
        } else if (rating >= 3) {
            return "text-amber-600 dark:text-yellow-400";
        } else if (rating >= 2) {
            return "text-orange-600 dark:text-orange-400";
        } else {
            return "text-red-600 dark:text-red-400";
        }
    };

    const calculateDifficultyColor = (difficulty: number | undefined) => {
        if (!difficulty) {
            return "";
        }
        if (difficulty <= 1) {
            return "text-green-600 dark:text-green-400";
        } else if (difficulty <= 2) {
            return "text-amber-600 dark:text-yellow-400";
        } else if (difficulty <= 3) {
            return "text-orange-600 dark:text-orange-400";
        } else {
            return "text-red-600 dark:text-red-400";
        }
    };

    let name = $derived(page.params.name)
    let currentName: string | null = null

    $effect(() => {
        if (name && name !== currentName) {
            currentName = name
            fetchInstructor(name)
        }
    })

</script>

<ContentWrapper>
    {#if $instructor}
        <div class="grid gap-4 lg:grid-cols-12">
            <div class="space-y-4 mt-2 lg:col-span-3">
                <Card>
                    <CardHeader class="pb-0 flex items-center">
                        <Avatar class="h-16 w-16">
                            <AvatarFallback class="text-2xl">{instructorName?.at(0)}</AvatarFallback>
                        </Avatar>
                        <CardTitle class="text-2xl font-bold">{instructorName}</CardTitle>
                        <CardTitle class="text-sm text-muted-foreground">{$instructor.official_name}</CardTitle>
                    </CardHeader>
                    <CardHeader
                            class="flex flex-row items-center justify-between space-y-0 pb-2"
                    >
                        <CardTitle class="text-base font-medium">Email</CardTitle>
                        <Mail class="text-muted-foreground h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                        <a href={`mailto:${$instructor.email}`} class="font-medium text-sm break-words underline underline-offset-4">{$instructor.email}</a>
                    </CardContent>
                    <CardHeader
                            class="flex flex-row items-center justify-between space-y-0 pb-2"
                    >
                        <CardTitle class="text-base font-medium">Position</CardTitle>
                        <BriefcaseBusiness class="text-muted-foreground h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                        <p class="text-sm break-words">{$instructor.position}</p>
                    </CardContent>
                    <CardHeader
                            class="flex flex-row items-center justify-between space-y-0 pb-2"
                    >
                        <CardTitle class="text-base font-medium">Department</CardTitle>
                        <University class="text-muted-foreground h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                        <p class="text-sm break-words">{$instructor.department}</p>
                    </CardContent>
                    <CardHeader
                            class="flex flex-row items-center justify-between space-y-0 pb-2"
                    >
                        <CardTitle class="text-base font-medium">Credentials</CardTitle>
                        <GraduationCap class="text-muted-foreground h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                        <p class="text-sm break-words">{$instructor.credentials}</p>
                    </CardContent>
                </Card>
            </div>
            <div class="mt-2 lg:col-span-9 space-y-4">
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <CardTitle class="text-sm font-medium">Grade Point Average</CardTitle>
                            <BookPlus class="text-muted-foreground h-4 w-4" />
                        </CardHeader>
                        <CardContent>
                            <div class="text-2xl font-bold">
                                Coming Soon
                            </div>
                            <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestTermGPA($course), getCumulativeGPA($course))} comparisonKeyword="Historical"/>-->
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
                                Coming Soon
                            </div>
                            <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestCompletionRate($course), getCumulativeCompletionRate($course))} comparisonKeyword="Historical"/>-->
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
                                Coming Soon
                            </div>
                            <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestARate($course), getCumulativeARate($course))} comparisonKeyword="Historical"/>-->
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader
                                class="flex flex-row items-center justify-between space-y-0 pb-2"
                        >
                            <CardTitle class="text-sm font-medium">Students</CardTitle>
                            <Users class="text-muted-foreground h-4 w-4" />
                        </CardHeader>
                        <CardContent>
                            <div class="text-2xl font-bold">
                                Coming Soon
                            </div>
                            <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestClassSize($course), getCumulativeClassSize($course))} comparisonKeyword="Historical"/>-->
                        </CardContent>
                    </Card>
                </div>
                {#if $instructor.rmp_data}
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Rating</CardTitle>
                                <Star class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold {calculateRatingColor($instructor.rmp_data.average_rating)}">
                                    {$instructor.rmp_data.average_rating.toFixed(1)}
                                </div>
                                <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestTermGPA($course), getCumulativeGPA($course))} comparisonKeyword="Historical"/>-->
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Difficulty</CardTitle>
                                <PencilRuler class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold {calculateDifficultyColor($instructor.rmp_data.average_difficulty)}">
                                    {$instructor.rmp_data.average_difficulty.toFixed(1)}
                                </div>
                                <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestCompletionRate($course), getCumulativeCompletionRate($course))} comparisonKeyword="Historical"/>-->
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Would Take Again</CardTitle>
                                <Repeat class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold">
                                    {$instructor.rmp_data?.would_take_again_percent.toFixed(1)}%
                                </div>
                                <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestARate($course), getCumulativeARate($course))} comparisonKeyword="Historical"/>-->
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader
                                    class="flex flex-row items-center justify-between space-y-0 pb-2"
                            >
                                <CardTitle class="text-sm font-medium">Attendance</CardTitle>
                                <Users class="text-muted-foreground h-4 w-4" />
                            </CardHeader>
                            <CardContent>
                                <div class="text-2xl font-bold">
                                    {attendanceRequirement.most}
                                </div>
                                <p class="mt-0.5 text-xs">{(attendanceRequirement.count * 100 / attendanceRequirement.total).toFixed(1)}% of students reported.</p>
                            </CardContent>
                        </Card>
                    </div>
                    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
                        <Card>
                            <CardContent class="pt-6">
                                <RatingDonutChart ratingData={$instructor.rmp_data?.ratings_distribution} />
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent class="pt-6">
                                <AttendanceDonutChart attendanceData={$instructor.rmp_data?.mandatory_attendance} />
                            </CardContent>
                        </Card>
                    </div>
                {:else}
                    <Card>
                        <CardHeader class="pb-0">
                            <CardTitle class="text-lg font-bold">No Rate My Professors Data</CardTitle>
                            <CardDescription class="text-sm text-muted-foreground">This instructor does not have Rate My Professors data available.</CardDescription>
                        </CardHeader>
                    </Card>
                {/if}
                <Card>
                    <CardContent>
                        <InstructorWordCloud instructors={[$instructor]} />
                    </CardContent>
                </Card>
            </div>
        </div>
    {/if}
</ContentWrapper>