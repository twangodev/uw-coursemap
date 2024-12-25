type Ratings = {
    comment: string,
    difficulty_rating: number,
    quality_rating: number,
}

export type Instructor = {
    average_rating: number,
    ratings: Ratings[],
}

export type FullInstructorInformation = {
    name: string,
    email: string,
    data: Instructor | null
}