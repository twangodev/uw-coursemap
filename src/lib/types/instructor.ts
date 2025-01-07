export type MandatoryAttendance = {
    neither: number,
    no: number,
    total: number,
    yes: number,
}

const attendanceLabels: Record<keyof Omit<MandatoryAttendance, "total">, string> = {
    neither: "Unknown",
    no: "Optional",
    yes: "Required",
};

export type AttendanceRequirement = {
    most: string,
    count: number,
    total: number,
}

/**
 * Returns the attendance requirement with the highest count.
 * "total" is skipped since it's presumably an aggregate.
 */
export function getAttendanceRequirement(data: MandatoryAttendance | undefined): AttendanceRequirement {
    if (!data) {
        return {
            most: "Unknown",
            count: 0,
            total: 0,
        }
    }

    const relevantKeys = ["neither", "no", "yes"] as const;

    // Identify the key among neither/no/yes that has the highest value.
    const largestKey = relevantKeys.reduce((acc, key) => {
        return data[key] > data[acc] ? key : acc;
    }, "neither");

    // Build and return the result object
    return {
        most: attendanceLabels[largestKey],
        count: data[largestKey],
        total: data.total
    };
}

type Ratings = {
    comment: string,
    difficulty_rating: number,
    quality_rating: number,
}

export type RatingsDistribution = {
    r1: number,
    r2: number,
    r3: number,
    r4: number,
    r5: number,
    total: number,
}

export type Instructor = {
    average_difficulty: number,
    average_rating: number,
    id: string,
    legacy_id: string,
    mandatory_attendance: MandatoryAttendance,
    num_ratings: number,
    ratings: Ratings[],
    ratings_distribution: RatingsDistribution,
    would_take_again_percent: number,
}

export type FullInstructorInformation = {
    name: string,
    email: string,
    credentials: string | null,
    department: string | null,
    official_name: string | null,
    position: string | null,
    rmp_data: Instructor | null
}