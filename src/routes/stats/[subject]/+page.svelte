<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";
  import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import {
    ARateDataCard,
    CompletionRateDataCard,
    GPADataCard,
  } from "$lib/components/data-card/index.js";
  import ComboGradeDataStackedAreaChart from "$lib/components/charts/combo-grade-data-stacked-area-chart.svelte";
  import CourseTreemapChart from "$lib/components/charts/course-treemap-chart.svelte";
  import EnrollmentOverTermsChart from "$lib/components/charts/enrollment-over-terms-chart.svelte";
  import GradeDataHorizontalBarChart from "$lib/components/charts/grade-data-horizontal-bar-chart.svelte";
  import {
    calculateARate,
    calculateCompletionRate,
    calculateGradePointAverage,
  } from "$lib/types/madgrades.ts";
  import type { TermData } from "$lib/types/course.ts";
  import { BookOpen, Waypoints } from "@lucide/svelte";
  import { buttonVariants } from "$lib/components/ui/button/index.js";
  import { m } from "$lib/paraglide/messages";
  import { localizeHref } from "$lib/paraglide/runtime";

  let { data } = $props();

  let { subject, subjectFullName, stats, terms } = $derived(data);

  let gradesByTerm = $derived(stats.grades_by_term ?? {});
  let hasTermData = $derived(Object.keys(gradesByTerm).length > 0);
  let hasCourses = $derived((stats.courses?.length ?? 0) > 0);

  let latestGradeData = $derived.by(() => {
    const termCodes = Object.keys(gradesByTerm).sort(
      (a, b) => Number(a) - Number(b),
    );
    const latest = termCodes.at(-1);
    return latest ? gradesByTerm[latest] : null;
  });

  let comboTermData: { [key: string]: TermData } = $derived(
    Object.fromEntries(
      Object.entries(gradesByTerm).map(([term, gradeData]) => [
        term,
        { enrollment_data: null, grade_data: gradeData },
      ]),
    ),
  );

  let cumulativeGPA = $derived(
    calculateGradePointAverage(stats.total_grades_given),
  );
  let termGPA = $derived(
    calculateGradePointAverage(latestGradeData) ?? cumulativeGPA,
  );
  let cumulativeCompletionRate = $derived(
    calculateCompletionRate(stats.total_grades_given),
  );
  let termCompletionRate = $derived(
    calculateCompletionRate(latestGradeData) ?? cumulativeCompletionRate,
  );
  let cumulativeARate = $derived(calculateARate(stats.total_grades_given));
  let termARate = $derived(calculateARate(latestGradeData) ?? cumulativeARate);
</script>

<ContentWrapper>
  <PageHeader>
    <PageHeaderHeading>{subjectFullName}</PageHeaderHeading>
    <PageHeaderDescription class="text-muted-foreground">
      {m["stats.subject.description"]({ name: subjectFullName })}
    </PageHeaderDescription>
    <a
      href={localizeHref(`/explorer/${subject}`)}
      class={buttonVariants({ variant: "outline" })}
    >
      <Waypoints class="mr-2 size-4" />
      {m["stats.subject.viewCourseMap"]()}
    </a>
  </PageHeader>

  <section class="my-4 space-y-4">
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <GPADataCard {termGPA} {cumulativeGPA} />
      <CompletionRateDataCard {termCompletionRate} {cumulativeCompletionRate} />
      <ARateDataCard {termARate} {cumulativeARate} />
      <Card>
        <CardHeader
          class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
          <CardTitle class="text-sm font-medium">
            {m["stats.subject.totalCourses"]()}
          </CardTitle>
          <BookOpen class="text-muted-foreground h-4 w-4" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {stats.total_courses.toLocaleString()}
          </div>
          <p class="text-muted-foreground mt-0.5 text-xs">
            {m["stats.subject.gradesGiven"]({
              count: stats.total_grades_given.total.toLocaleString(),
            })}
          </p>
        </CardContent>
      </Card>
    </div>

    {#if hasTermData}
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardContent class="pt-6">
            <EnrollmentOverTermsChart {gradesByTerm} {terms} />
          </CardContent>
        </Card>
        <Card>
          <CardContent class="pt-6">
            <GradeDataHorizontalBarChart
              cumulative={stats.total_grades_given}
              termData={comboTermData}
              {terms}
            />
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardContent class="pt-6">
          <ComboGradeDataStackedAreaChart term_data={comboTermData} {terms} />
        </CardContent>
      </Card>
    {/if}

    {#if hasCourses}
      <Card>
        <CardContent class="pt-6">
          <CourseTreemapChart courses={stats.courses ?? []} />
        </CardContent>
      </Card>
    {/if}

    {#if !hasTermData && !hasCourses}
      <p class="text-muted-foreground my-8 text-center">
        {m["stats.subject.noData"]()}
      </p>
    {/if}
  </section>
</ContentWrapper>
