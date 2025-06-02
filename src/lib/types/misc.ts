import type {GradeData} from "$lib/types/madgrades.ts";
import type { CourseReference } from "./course";

export type QuickStatistics = {
    top_100_a_rate_chances: {
        a_rate_chance: number,
        reference: CourseReference
    }[],
    most_rated_instructors: string[],
    total_courses: number,
    total_grades_given: GradeData,
    total_instructors: number,
    total_detected_requisites: number,
    total_ratings: number,
}