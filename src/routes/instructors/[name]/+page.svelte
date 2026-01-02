<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import { getAttendanceRequirement } from "$lib/types/instructor.ts";
  import {
    BookA,
    BookPlus,
    BriefcaseBusiness,
    CircleCheckBig,
    GraduationCap,
    Mail,
    PencilRuler,
    Repeat,
    Star,
    University,
    Users,
  } from "@lucide/svelte";
  import { Card, CardContent, CardHeader } from "$lib/components/ui/card";
  import { CardDescription, CardTitle } from "$lib/components/ui/card/index.js";
  import RatingDonutChart from "$lib/components/charts/rating-donut-chart.svelte";
  import AttendanceDonutChart from "$lib/components/charts/attendance-donut-chart.svelte";
  import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
  import {
    calculateARate,
    calculateCompletionRate,
    calculateGradePointAverage,
  } from "$lib/types/madgrades.ts";
  import { InstructorDetails } from "$lib/components/instructor";

  let { data } = $props();
  let instructor = $derived(data.instructor);

  let attendanceRequirement = $derived(
    getAttendanceRequirement(instructor?.rmp_data?.mandatory_attendance),
  );

  const calculateRatingColor = (rating: number | null | undefined) => {
    if (rating == null) {
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

  const calculateDifficultyColor = (difficulty: number | null | undefined) => {
    if (difficulty == null) {
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

  const appendPercent = (value: number | null) => {
    if (value === null) {
      return "Not Reported";
    }
    return `${value.toFixed(2)}%`;
  };
</script>

<ContentWrapper>
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-12">
    <InstructorDetails {instructor} />
    <div class="mt-2 grid-cols-1 space-y-4 lg:col-span-9">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader
            class="flex flex-row items-center justify-between space-y-0 pb-2"
          >
            <CardTitle class="text-sm font-medium"
              >Grade Point Average</CardTitle
            >
            <BookPlus class="text-muted-foreground h-4 w-4" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">
              {calculateGradePointAverage(
                instructor.cumulative_grade_data,
              )?.toFixed(2) ?? "Not Reported"}
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
              {appendPercent(
                calculateCompletionRate(instructor.cumulative_grade_data),
              )}
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
              {appendPercent(calculateARate(instructor.cumulative_grade_data))}
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
              {instructor?.cumulative_grade_data?.total ?? 0}
            </div>
            <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestClassSize($course), getCumulativeClassSize($course))} comparisonKeyword="Historical"/>-->
          </CardContent>
        </Card>
      </div>
      {#if instructor.rmp_data}
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader
              class="flex flex-row items-center justify-between space-y-0 pb-2"
            >
              <CardTitle class="text-sm font-medium">Rating</CardTitle>
              <Star class="text-muted-foreground h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div
                class="text-2xl font-bold {calculateRatingColor(
                  instructor.rmp_data.average_rating,
                )}"
              >
                {instructor.rmp_data.average_rating?.toFixed(1) ?? "N/A"}
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
              <div
                class="text-2xl font-bold {calculateDifficultyColor(
                  instructor.rmp_data.average_difficulty,
                )}"
              >
                {instructor.rmp_data.average_difficulty?.toFixed(1) ?? "N/A"}
              </div>
              <!--                            <Change class="mt-0.5 text-xs" points={getPercentChange(getLatestCompletionRate($course), getCumulativeCompletionRate($course))} comparisonKeyword="Historical"/>-->
            </CardContent>
          </Card>
          <Card>
            <CardHeader
              class="flex flex-row items-center justify-between space-y-0 pb-2"
            >
              <CardTitle class="text-sm font-medium">Would Take Again</CardTitle
              >
              <Repeat class="text-muted-foreground h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">
                {instructor.rmp_data?.would_take_again_percent?.toFixed(1) ?? "N/A"}%
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
              <p class="mt-0.5 text-xs">
                {(
                  (attendanceRequirement.count * 100) /
                  attendanceRequirement.total
                ).toFixed(1)}% of students reported.
              </p>
            </CardContent>
          </Card>
        </div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <CardContent class="pt-6">
              <RatingDonutChart
                ratingData={instructor.rmp_data?.ratings_distribution}
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent class="pt-6">
              <AttendanceDonutChart
                attendanceData={instructor.rmp_data?.mandatory_attendance}
              />
            </CardContent>
          </Card>
        </div>
      {:else}
        <Card>
          <CardHeader class="pb-0">
            <CardTitle class="text-lg font-bold"
              >No Rate My Professors Data</CardTitle
            >
            <CardDescription class="text-muted-foreground text-sm"
              >This instructor does not have Rate My Professors data available.</CardDescription
            >
          </CardHeader>
        </Card>
      {/if}
      <Card>
        <CardContent>
          <InstructorWordCloud instructors={[instructor]} />
        </CardContent>
      </Card>
      {#if instructor.rmp_data?.ratings?.length}
        <Card class="mt-4">
          <CardHeader class="pb-2">
            <CardTitle class="text-lg font-bold">Comments</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              class="custom-scrollbar max-h-64 space-y-3 overflow-y-auto pt-4"
            >
              {#each instructor.rmp_data.ratings as rating}
                {#if rating.comment}
                  <div class="bg-muted-foreground/5 rounded-lg border p-3">
                    <p class="text-sm">{rating.comment}</p>
                  </div>
                {/if}
              {/each}
            </div>
          </CardContent>
        </Card>
      {/if}
    </div>
  </div>
</ContentWrapper>

<style>
  /* Nicer, thinner scrollbar styling */
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(100, 100, 100, 0.4);
    border-radius: 3px;
  }
  .custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background-color: rgba(100, 100, 100, 0.6);
  }
  /* Firefox support */
  .custom-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(100, 100, 100, 0.4) transparent;
  }
</style>
