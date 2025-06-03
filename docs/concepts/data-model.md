# Data Model

To standardize the wide variety of data sources, we have created a language-agnostic common data model that all data sources must conform to. This model is designed to be flexible and extensible, allowing for the addition of new data sources and fields as needed.

At some point we'll migrate this to an OAS 3.0 spec, but for now, this we'll just describe the model in markdown.

## Courses

For now, just look in the typescript type definition, under `./src/lib/types/course.ts`.

## Instructors

You'll be using the `FullInstructor` type from `./src/lib/types/instructor.ts`.


## Experimental Data

The following data models may be removed, changed, or added to in the future. They are experimental and you should not rely on them for production use.

- Whatever API not under `/course/` or `/instructors/` is experimental.





