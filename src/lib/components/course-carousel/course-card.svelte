<script lang="ts">
  import {
    type Course,
    CourseUtils,
  } from "$lib/types/course.ts";
  import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import { localizeHref } from "$lib/paraglide/runtime";

  interface Props {
    course: Course;
  }

  let { course }: Props = $props();
</script>

<a href={localizeHref(`/courses/${CourseUtils.courseReferenceToSanitizedString(course.course_reference)}`)}>
  <Card class="w-full max-w-64 overflow-hidden">
    <CardHeader class="pb-0">
      <CardTitle class="truncate">{course.course_title}</CardTitle>
      <CardDescription class="truncate font-bold"
        >{CourseUtils.courseReferenceToString(course.course_reference)}</CardDescription
      >
      <CardDescription class="line-clamp-4"
        >{course.description}</CardDescription
      >
    </CardHeader>
  </Card>
</a>
