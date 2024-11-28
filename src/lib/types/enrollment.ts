type School = {
    name: string,
    abbreviation: string,
    url: string
}

export type EnrollmentData = {
    school: School,
    last_taught_term: string,
    typically_offered: string,
    credit_count: [number, number],
    general_education: boolean,
    ethnic_studies: boolean,
    instructors: {
        [instructor: string]: string
    }
}