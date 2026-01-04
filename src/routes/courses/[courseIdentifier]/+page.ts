import { getLatestTermId, type Terms } from "$lib/types/terms.ts";
import { createApiClient } from "$lib/api";
import {
  type Course,
  CourseUtils
} from "$lib/types/course.ts";
import { getFullInstructor } from "$lib/types/instructor.ts";
import { error } from "@sveltejs/kit";
import type { ElementDefinition } from "cytoscape";
import { generateCourseMetaDescription, generateCourseTitle, generateCourseOgImage } from "$lib/seo/course-seo.ts";
import { generateComprehensiveCourseJsonLd } from "$lib/seo/course-schema.ts";
import { generateCourseBreadcrumbSchema } from "$lib/seo/breadcrumb-schema.ts";

export const load = async ({ params, url, fetch }) => {
  const api = createApiClient(fetch);

  const { data: terms, error: termsError } = await api.GET("/terms");
  if (termsError || !terms)
    throw error(404, `Failed to fetch terms`);

  let latestTermId = getLatestTermId(terms as Terms);
  let selectedTermId = url.searchParams.get("term") || latestTermId;

  const { data: courseData, error: courseError } = await api.GET("/course/{courseId}", {
    params: { path: { courseId: params.courseIdentifier } },
  });
  if (courseError || !courseData)
    throw error(404, `Failed to fetch course`);

  let course = courseData;

  let similarCourseReferences = course.similar_courses;
  let similarCoursesPromises = similarCourseReferences.map(
    async (courseReference) => {
      const { data } = await api.GET("/course/{courseId}", {
        params: { path: { courseId: CourseUtils.courseReferenceToSanitizedString(courseReference) } },
      });
      if (!data)
        throw error(404, `Failed to fetch similar course`);
      return data;
    },
  );
  let similarCourses: Course[] = await Promise.all(similarCoursesPromises);

  let instructors = await getFullInstructor(
    course,
    terms as Terms,
    selectedTermId,
    fetch,
  );

  const { data: graphData, error: graphError } = await api.GET("/graphs/course/{courseId}", {
    params: { path: { courseId: CourseUtils.courseReferenceToSanitizedString(course.course_reference) } },
  });
  if (graphError || !graphData)
    throw error(404, `Failed to fetch prerequisite graph data`);

  const prerequisiteElementDefinitions = graphData as unknown as ElementDefinition[];
  prerequisiteElementDefinitions.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      item.data["title"] = "";
    }
  });

  const { data: prerequisiteStyleEntries, error: styleError } = await api.GET("/styles/{subject}", {
    params: { path: { subject: course.course_reference.subjects[0] } },
  });
  if (styleError || !prerequisiteStyleEntries)
    throw error(404, `Failed to fetch prerequisite style data`);

  const courseCode = CourseUtils.courseReferenceToString(course.course_reference);

  // Fetch meetings data
  let meetings = null;
  const { data: meetingsData } = await api.GET("/course/{courseId}/meetings", {
    params: { path: { courseId: CourseUtils.courseReferenceToSanitizedString(course.course_reference) } },
  });
  if (meetingsData) {
    meetings = meetingsData;
  } else {
    console.log(`No meetings data available for ${courseCode}`);
  }

  // Generate SEO content
  const metaDescription = generateCourseMetaDescription(course);
  const pageTitle = generateCourseTitle(course);
  const ogImage = generateCourseOgImage(course);

  // Generate comprehensive JSON-LD schemas
  const courseJsonLd = generateComprehensiveCourseJsonLd(course, instructors, terms as Terms, selectedTermId);
  const breadcrumbJsonLd = generateCourseBreadcrumbSchema(course);

  return {
    subtitle: pageTitle,
    description: metaDescription,
    ogImage,
    terms,
    selectedTermId,
    course,
    similarCourses,
    instructors,
    prerequisiteElementDefinitions,
    prerequisiteStyleEntries,
    meetings,
    jsonLd: [courseJsonLd, breadcrumbJsonLd],
  };
};
