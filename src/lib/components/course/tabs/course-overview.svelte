<script lang="ts">
  import { ArrowUpRight } from "@lucide/svelte";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import GradeDataHorizontalBarChart from "$lib/components/charts/grade-data-horizontal-bar-chart.svelte";
  import CourseCarousel from "$lib/components/course-carousel/course-carousel.svelte";
  import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
  import type { Course } from "$lib/types/course.ts";
  import type { Terms } from "$lib/types/terms.ts";
  import { type FullInstructorInformation } from "$lib/types/instructor.ts";
  import {
    calculateARate,
    calculateCompletionRate,
    calculateGradePointAverage,
  } from "$lib/types/madgrades.ts";
  import {
    ARateDataCard,
    ClassSizeDataCard,
    CompletionRateDataCard,
    GPADataCard,
  } from "$lib/components/data-card/index.js";

  interface Props {
    course: Course;
    similarCourses: Course[];
    terms: Terms;
    selectedTerm: string | undefined;
    instructors: FullInstructorInformation[];
    goToInstructors: () => void;
  }

  let {
    course,
    similarCourses,
    terms,
    selectedTerm,
    instructors,
    goToInstructors,
  }: Props = $props();

  function termsWithGradeData(course: Course) {
    const allTerms = Object.keys(course?.term_data ?? {}).sort(
      (a, b) => Number(a) - Number(b),
    );
    return allTerms.filter(
      (term) => course.term_data[term]?.grade_data != null,
    );
  }

  function getTermGradeData(course: Course) {
    const validTerms = termsWithGradeData(course);
    if (!validTerms.length) return null;
    const latestTerm = validTerms[validTerms.length - 1];

    let candidateTerm = selectedTerm ?? latestTerm;
    return (
      course.term_data[candidateTerm]?.grade_data ??
      course.term_data[latestTerm].grade_data
    );
  }

  const getLatestTermGPA = (course: Course) => {
    return calculateGradePointAverage(getTermGradeData(course));
  };

  function getCumulativeGPA(course: Course) {
    return calculateGradePointAverage(course?.cumulative_grade_data);
  }

  const getLatestCompletionRate = (course: Course) => {
    return calculateCompletionRate(getTermGradeData(course));
  };

  const getCumulativeARate = (course: Course) => {
    return calculateARate(course.cumulative_grade_data);
  };

  const getLatestARate = (course: Course) => {
    return calculateARate(getTermGradeData(course));
  };

  const getCumulativeClassSize = (course: Course) => {
    return (
      (course.cumulative_grade_data?.total ?? 0) /
      termsWithGradeData(course).length
    );
  };

  const getLatestClassSize = (course: Course) => {
    return getTermGradeData(course)?.total ?? 0;
  };

  const getCumulativeCompletionRate = (course: Course) => {
    return calculateCompletionRate(course.cumulative_grade_data);
  };

  let termGPA = $derived(getLatestTermGPA(course));
  let cumulativeGPA = $derived(getCumulativeGPA(course));
  let termCompletionRate = $derived(getLatestCompletionRate(course));
  let cumulativeCompletionRate = $derived(getCumulativeCompletionRate(course));
  let termARate = $derived(getLatestARate(course));
  let cumulativeARate = $derived(getCumulativeARate(course));
  let termClassSize = $derived(getLatestClassSize(course));
  let cumulativeAverageClassSize = $derived(getCumulativeClassSize(course));
</script>

<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
  <GPADataCard {termGPA} {cumulativeGPA} />
  <CompletionRateDataCard {termCompletionRate} {cumulativeCompletionRate} />
  <ARateDataCard {termARate} {cumulativeARate} />
  <ClassSizeDataCard {termClassSize} {cumulativeAverageClassSize} />
</div>
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-7">
  <Card class="lg:col-span-4">
    <CardContent class="pt-6">
      {#if course.cumulative_grade_data}
        <GradeDataHorizontalBarChart
          cumulative={course.cumulative_grade_data}
          termData={course.term_data}
          term={selectedTerm}
          {terms}
        />
      {:else}
        <p class="text-center">No data available</p>
      {/if}
    </CardContent>
  </Card>
  <Card class="lg:col-span-3">
    <CardHeader>
      <CardTitle
        >Instructors ({selectedTerm ? terms[selectedTerm] : ""})</CardTitle
      >
      <CardDescription class="flex">
        Sorted by ratings from
        <a
          class="ml-1 flex items-center font-medium underline-offset-4 hover:underline"
          href="https://www.ratemyprofessors.com/"
          target="_blank"
        >
          Rate My Professors
          <ArrowUpRight class="inline h-4 w-4" />
        </a>
      </CardDescription>
    </CardHeader>
    <CardContent>
      {#key instructors}
        {#each instructors.slice(0, 3) as instructor}
          <InstructorPreview {instructor} showRating={true} />
        {/each}
      {/key}
      {#if instructors.length > 3}
        <div class="flex justify-center">
          <button
            class="text-muted-foreground flex items-center space-x-1 text-center text-xs hover:cursor-pointer hover:underline"
            onclick={goToInstructors}
          >
            <span>Showing 3 of {instructors.length} instructors.</span>
            <ArrowUpRight class="h-3.5 w-3.5" />
          </button>
        </div>
      {/if}
    </CardContent>
  </Card>
  <div class="md:col-span-2 lg:col-span-7">
    <h2 class="my-4 text-2xl font-bold">Similar Courses</h2>
    <CourseCarousel courses={similarCourses} />
  </div>
</div>
