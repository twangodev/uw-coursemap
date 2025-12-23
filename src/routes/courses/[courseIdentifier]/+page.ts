import { getLatestTermId, type Terms } from "$lib/types/terms.ts";
import { env } from "$env/dynamic/public";
import {
  type Course,
  CourseUtils
} from "$lib/types/course.ts";
import { getFullInstructorInformation } from "$lib/types/instructor.ts";
import { error } from "@sveltejs/kit";
import type { ElementDefinition } from "cytoscape";
import { generateCourseMetaDescription, generateCourseTitle, generateCourseOgImage } from "$lib/seo/course-seo.ts";
import { generateComprehensiveCourseJsonLd } from "$lib/seo/course-schema.ts";
import { generateCourseBreadcrumbSchema } from "$lib/seo/breadcrumb-schema.ts";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ params, url, fetch }) => {
  let termsResponse = await fetch(`${PUBLIC_API_URL}/terms.json`);
  if (!termsResponse.ok)
    throw error(
      termsResponse.status,
      `Failed to fetch terms: ${termsResponse.statusText}`,
    );
  let terms: Terms = await termsResponse.json();

  let latestTermId = getLatestTermId(terms);
  let selectedTermId = url.searchParams.get("term") || latestTermId;

  let courseResponse = await fetch(
    `${PUBLIC_API_URL}/course/${params.courseIdentifier}.json`,
  );
  if (!courseResponse.ok)
    throw error(
      courseResponse.status,
      `Failed to fetch course: ${courseResponse.statusText}`,
    );
  let course: Course = await courseResponse.json();

  let similarCourseReferences = course.similar_courses;
  let similarCoursesPromises = similarCourseReferences.map(
    async (courseReference) => {
      let courseResponse = await fetch(
        `${PUBLIC_API_URL}/course/${CourseUtils.sanitizeCourseReferenceToString(courseReference)}.json`,
      );
      if (!courseResponse.ok)
        throw error(
          courseResponse.status,
          `Failed to fetch similar course: ${courseResponse.statusText}`,
        );
      return await courseResponse.json();
    },
  );
  let similarCourses: Course[] = await Promise.all(similarCoursesPromises);

  let instructors = await getFullInstructorInformation(
    course,
    terms,
    selectedTermId,
    fetch,
  );

  const prerequisiteElementDefinitionsResponse = await fetch(
    `${PUBLIC_API_URL}/graphs/course/${CourseUtils.sanitizeCourseReferenceToString(course.course_reference)}.json`,
  );
  if (!prerequisiteElementDefinitionsResponse.ok)
    throw error(
      prerequisiteElementDefinitionsResponse.status,
      `Failed to fetch prerequisite graph data: ${prerequisiteElementDefinitionsResponse.statusText}`,
    );
  const prerequisiteElementDefinitions: ElementDefinition[] =
    await prerequisiteElementDefinitionsResponse.json();

  prerequisiteElementDefinitions.forEach((item: any) => {
    item["pannable"] = true;
    if (!Object.hasOwn(item.data, "title")) {
      item.data["title"] = "";
    }
  });

  const styleEntriesResponse = await fetch(
    `${PUBLIC_API_URL}/styles/${course.course_reference.subjects[0]}.json`,
  );
  if (!styleEntriesResponse.ok)
    throw error(
      styleEntriesResponse.status,
      `Failed to fetch prerequisite style data: ${styleEntriesResponse.statusText}`,
    );
  const prerequisiteStyleEntries = await styleEntriesResponse.json();

  const courseCode = CourseUtils.courseReferenceToString(course.course_reference);
  
  // Fetch meetings data
  let meetings = null;
  try {
    const meetingsResponse = await fetch(
      `${PUBLIC_API_URL}/course/${CourseUtils.sanitizeCourseReferenceToString(course.course_reference)}/meetings.json`,
    );
    if (meetingsResponse.ok) {
      meetings = await meetingsResponse.json();
    }
  } catch (e) {
    console.log(`No meetings data available for ${courseCode}`);
  }
  
  // Generate SEO content
  const metaDescription = generateCourseMetaDescription(course);
  const pageTitle = generateCourseTitle(course);
  const ogImage = generateCourseOgImage(course);

  // Generate comprehensive JSON-LD schemas
  const courseJsonLd = generateComprehensiveCourseJsonLd(course, instructors, terms, selectedTermId);
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
