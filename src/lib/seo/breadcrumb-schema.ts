import type { BreadcrumbList, WithContext, ListItem } from "schema-dts";
import type { Course } from "$lib/types/course.ts";
import { courseReferenceToString } from "$lib/types/course.ts";

export function generateCourseBreadcrumbSchema(course: Course): WithContext<BreadcrumbList> {
  const courseCode = courseReferenceToString(course.course_reference);
  
  const breadcrumbItems: ListItem[] = [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://uwcourses.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Courses",
      "item": "https://uwcourses.com/courses"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": courseCode,
      "item": `https://uwcourses.com/courses/${courseCode.replace(/[\s\/]/g, '_')}`
    }
  ];
  
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": breadcrumbItems
  };
}

