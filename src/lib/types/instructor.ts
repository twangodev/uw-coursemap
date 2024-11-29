export type Instructor = {
    average_rating: number
}

export type FullInstructorInformation = {
    name: string,
    email: string,
    data: Instructor | null
}