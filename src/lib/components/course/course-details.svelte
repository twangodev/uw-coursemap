<script lang="ts">
  import {
    BookOpen,
    CalendarRange,
    ClipboardCheck,
    Info,
  } from "@lucide/svelte";
  import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import type { Course } from "$lib/types/course.ts";
  import type { FullInstructorInformation } from "$lib/types/instructor.ts";
  import ClampedParagraph from "../clamped-paragraph.svelte";
  import LinkedPrerequisites from "./linked-prerequisites.svelte";
  import SatisfiedRequisites from "./satisfied-requisites.svelte";
  import CourseSummary from "./course-summary.svelte";
  import { m } from "$lib/paraglide/messages";

  interface Props {
    course: Course;
    selectedTerm: string | undefined;
    instructors: FullInstructorInformation[];
  }

  let { course, selectedTerm, instructors }: Props = $props();

  function termsWithEnrollmentData(course: Course) {
    const allTerms = Object.keys(course?.term_data ?? {}).sort(
      (a, b) => Number(a) - Number(b),
    );
    return allTerms.filter(
      (term) => course.term_data[term]?.enrollment_data != null,
    );
  }

  function getLatestEnrollmentData(course: Course) {
    const validTerms = termsWithEnrollmentData(course);
    if (!validTerms.length) return null;
    const latestTerm = validTerms[validTerms.length - 1];

    let candidateTerm = selectedTerm ?? latestTerm;
    return (
      course.term_data[candidateTerm]?.enrollment_data ??
      course.term_data[latestTerm].enrollment_data
    );
  }

  const getCreditCount = (course: Course) => {
    const creditCount = getLatestEnrollmentData(course)?.credit_count;
    if (!creditCount) {
      return m["course.details.notReported"]();
    }

    if (creditCount[0] === creditCount[1]) {
      return `${creditCount[0]}`;
    } else {
      return m["course.details.creditsRange"]({
        min: creditCount[0],
        max: creditCount[1]
      });
    }
  };

  const getNormallyOffered = (course: Course) => {
    return getLatestEnrollmentData(course)?.typically_offered ?? m["course.details.notReported"]();
  };
</script>

<div class="mt-2 space-y-4 lg:col-span-3">
  <Card>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">{m["course.details.courseDescription"]()}</CardTitle>
      <Info class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      <ClampedParagraph clampAmount={5} class="text-sm break-words">
        {course.description}
      </ClampedParagraph>
    </CardContent>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">{m["course.details.prerequisites"]()}</CardTitle>
      <BookOpen class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    {#key course}
      <CardContent>
        <ClampedParagraph clampAmount={3} class="text-sm break-words">
          <LinkedPrerequisites {course} />
        </ClampedParagraph>
      </CardContent>
      <CardHeader
        class="flex flex-row items-center justify-between space-y-0 pb-2"
      >
        <CardTitle class="text-base font-medium">{m["course.details.satisfies"]()}</CardTitle>
        <BookOpen class="text-muted-foreground h-4 w-4" />
      </CardHeader>
      <CardContent>
        <ClampedParagraph clampAmount={2} class="text-sm break-words">
          <SatisfiedRequisites {course} />
        </ClampedParagraph>
      </CardContent>
    {/key}
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <CardHeader
          class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
          <CardTitle class="text-base font-medium">{m["course.details.credits"]()}</CardTitle>
          <ClipboardCheck class="text-muted-foreground h-4 w-4" />
        </CardHeader>
        <CardContent>
          <p class="text-sm break-words">{getCreditCount(course)}</p>
        </CardContent>
      </div>
      <div class="flex-1">
        <CardHeader
          class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
          <CardTitle class="text-base font-medium">{m["course.details.offered"]()}</CardTitle>
          <CalendarRange class="text-muted-foreground h-4 w-4" />
        </CardHeader>
        <CardContent>
          <p class="text-sm break-words">{getNormallyOffered(course)}</p>
        </CardContent>
      </div>
    </div>
  </Card>
  <CourseSummary {course} {instructors} />
</div>
