import asyncio

import numpy as np

from course import Course
from embeddings import get_openai_client, get_embedding, cosine_similarity, normalize
from enrollment_data import GradeData
from instructors import FullInstructor

def quick_statistics(course_ref_to_course: dict[Course.Reference, Course], logger):

    total_courses = len(course_ref_to_course)
    school_cumulative_grades = GradeData.empty()

    for course, course_data in course_ref_to_course.items():
        cumulative_grade_data = course_data.cumulative_grade_data
        if cumulative_grade_data:
            school_cumulative_grades = school_cumulative_grades.merge_with(cumulative_grade_data)

    logger.info("Total courses: %d", total_courses)
    logger.info("School cumulative grades: %s", school_cumulative_grades)

    return {
        "total_courses": total_courses,
        "total_grades_given": school_cumulative_grades,
    }

async def course_embedding_analysis(course_ref_to_course: dict[Course.Reference, Course], cache_dir, openai_api_key, model, logger):

    open_ai_client = get_openai_client(
        api_key=openai_api_key,
        logger=logger,
    )

    total_courses = len(course_ref_to_course)
    # Use a mutable dictionary to track progress.
    progress = {"completed": 0}
    # Create a lock to ensure that updates to the progress counter are thread-safe.
    lock = asyncio.Lock()

    async def embed_course(course_ref, course):
        summary = course.get_short_summary()
        # Wrap the synchronous get_embedding call in asyncio.to_thread if necessary.
        embedding = await asyncio.to_thread(get_embedding, cache_dir, open_ai_client, model, summary, logger)

        # Update progress safely using the lock.
        async with lock:
            progress["completed"] += 1
            logger.debug("Progress: %d/%d courses completed", progress["completed"], total_courses)
        return course_ref, embedding

    # Create tasks for all courses.
    tasks = [
        embed_course(course_ref, course)
        for course_ref, course in course_ref_to_course.items()
    ]

    # Await tasks concurrently.
    results = await asyncio.gather(*tasks)

    # Build the final embeddings dictionary.
    course_embeddings = {course_ref: embedding for course_ref, embedding in results}

    logger.info("Course embeddings pulled for %d courses", len(course_embeddings))

    subject_to_course = {}

    for course_ref, course in course_ref_to_course.items():

        subjects = course_ref.subjects

        for subject in subjects:

            if subject not in subject_to_course:
                subject_to_course[subject] = []
            subject_to_course[subject].append(course_ref)

    def get_similar_courses_prompt(prompt, min_cc=0, max_cc=1000, length=5):

        existential_crisis = normalize(get_embedding(cache_dir, open_ai_client, model, prompt, logger))

        existential_crisis_similarity = {
            course_ref: cosine_similarity(existential_crisis, embedding)
            for course_ref, embedding in course_embeddings.items() if max_cc >= course_ref.course_number >= min_cc
        }

        sorted_crisis = sorted(existential_crisis_similarity.items(), key=lambda x: x[1], reverse=True)

        return sorted_crisis[:5]

    def get_similar_courses(course: Course, length=5):
        return get_similar_courses_prompt(
            course.get_short_summary(),
            length=length
        )

def aggregate_courses(course_ref_to_course: dict[Course.Reference, Course], cache_dir, openai_api_key, model, logger):
    qs = quick_statistics(course_ref_to_course, logger)

    asyncio.run(course_embedding_analysis(course_ref_to_course, cache_dir, openai_api_key, model, logger))

    return qs

def aggregate_instructors(course_ref_to_course: dict[Course.Reference, Course], instructor_to_rating: dict[str, FullInstructor], logger):

    for course in course_ref_to_course.values():
        for term_data in course.term_data.values():

            if not term_data.grade_data or not term_data.grade_data.instructors:
                continue

            for instructor_name in term_data.grade_data.instructors:

                if instructor_name not in instructor_to_rating:
                    continue

                instructor = instructor_to_rating[instructor_name]

                if not instructor.courses_taught:
                    instructor.courses_taught = set()

                if not instructor.cumulative_grade_data:
                    instructor.cumulative_grade_data = GradeData.empty()

                course_reference = course.course_reference
                grade_data_summation = instructor.cumulative_grade_data.merge_with(term_data.grade_data)

                instructor.courses_taught.add(course_reference.get_identifier())
                instructor.cumulative_grade_data = grade_data_summation

