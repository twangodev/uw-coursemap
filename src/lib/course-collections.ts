export const courseCollections = {
  easiest: {
    title: "Easiest courses",
    description:
      "Looking for a gentler semester? Start with courses where students have earned higher grades.",
    method: "Highest historical GPA first.",
  },
  hardest: {
    title: "Hardest courses",
    description:
      "Plan ahead for courses where students have earned lower grades.",
    method: "Lowest historical GPA first.",
  },
} as const;
export type CourseCollection = keyof typeof courseCollections;
export const isCourseCollection = (value: string): value is CourseCollection =>
  Object.hasOwn(courseCollections, value);
