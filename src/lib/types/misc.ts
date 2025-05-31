import type {GradeData} from "$lib/types/madgrades.ts";

export type QuickStatistics = {
    total_courses: number,
    total_grades_given: GradeData,
    total_instructors: number,
    total_ratings: number,
}