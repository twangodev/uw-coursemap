type MandatoryAttendance = {
    neither: number,
    no: number,
    total: number,
    yes: number,
}

type Ratings = {
    comment: string,
    difficulty_rating: number,
    quality_rating: number,
}

type RatingsDistribution = {
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
    num_ratings: number,
    ratings: Ratings[],
    ratings_distribution: RatingsDistribution,
    would_take_again_percent: number,
}

export type FullInstructorInformation = {
    name: string,
    email: string,
    data: Instructor | null
}