import type { GradeData } from "$lib/types/madgrades.ts";
import type { CourseReference } from "$lib/types/course.ts";

export type SubjectCourseStat = {
  course_reference: CourseReference;
  course_title: string;
  grades_given: number;
  gpa: number | null;
};

export type SubjectStats = {
  total_courses: number;
  total_grades_given: GradeData;
  total_detected_requisites: number;
  // absent from stats JSON generated before these fields existed
  grades_by_term?: { [term: string]: GradeData };
  courses?: SubjectCourseStat[];
};
