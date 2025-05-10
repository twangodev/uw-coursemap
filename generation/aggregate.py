import asyncio

import numpy as np

from course import Course
from embeddings import get_model, get_embedding, cosine_similarity, normalize
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

async def course_embedding_analysis(course_ref_to_course: dict[Course.Reference, Course], cache_dir, logger):

    model = get_model(cache_dir, logger)

    total_courses = len(course_ref_to_course)
    # Use a mutable dictionary to track progress.
    progress = {"completed": 0}
    # Create a lock to ensure that updates to the progress counter are thread-safe.
    lock = asyncio.Lock()

    async def embed_course(course_ref, course):
        summary = course.get_short_summary()
        # Wrap the synchronous get_embedding call in asyncio.to_thread if necessary.
        embedding = await asyncio.to_thread(get_embedding, cache_dir, model, summary, logger)

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

    # Build the dictionary mapping course references to their embeddings.
    course_embeddings = {course_ref: embedding for course_ref, embedding in results}
    logger.info("Course embeddings pulled for %d courses", len(course_embeddings))

    # --- Vectorized Nearest Neighbor Computation ---
    # Prepare an ordered list of course references and a corresponding NumPy matrix of embeddings.
    course_refs = list(course_embeddings.keys())
    embeddings = np.stack([course_embeddings[ref] for ref in course_refs])

    # For filtering purposes, extract the course numbers.
    # (Assumes each course_ref has an attribute 'course_number'.)
    course_numbers = np.array([ref.course_number for ref in course_refs])
    # Define your filtering criteria.
    min_cc = 0
    max_cc = 1000
    k = 5

    # Create a global mask: only consider courses within the [min_cc, max_cc] range.
    allowed_mask = (course_numbers >= min_cc) & (course_numbers <= max_cc)

    # Compute the full similarity matrix between all courses.
    # (Assumes the embeddings are normalized so that cosine similarity = dot product.)
    similarity_matrix = np.dot(embeddings, embeddings.T)

    # For each course, disqualify courses that do not satisfy the filter by setting their similarity to -∞.
    similarity_matrix[:, ~allowed_mask] = -np.inf
    # Remove self similarity by setting the diagonal to -∞.
    np.fill_diagonal(similarity_matrix, -np.inf)

    # For each row in the similarity matrix, use argpartition to get the indices of the top k similar courses.
    top_k_indices = np.argpartition(similarity_matrix, -k, axis=1)[:, -k:]
    # Optionally sort these indices to order by descending similarity.
    sorted_top_k_indices = np.array([
        indices[np.argsort(similarity_matrix[i, indices])[::-1]]
        for i, indices in enumerate(top_k_indices)
    ])

    # Build a mapping from each course reference to its corresponding top k similar course references.
    similar_courses_mapping = {}
    for i, course_ref in enumerate(course_refs):
        similar_courses_mapping[course_ref] = [course_refs[j] for j in sorted_top_k_indices[i]]

    # Update each course with its similar courses.
    for course_ref, course in course_ref_to_course.items():
        logger.debug("Setting similar courses for %s", course_ref.get_identifier())
        # Use the mapping to update the course; here we assume each course has a .similar_courses attribute.
        course.similar_courses = [
            similar_ref
            for similar_ref in similar_courses_mapping.get(course_ref, [])
        ]

def aggregate_courses(course_ref_to_course: dict[Course.Reference, Course], cache_dir, logger):
    qs = quick_statistics(course_ref_to_course, logger)

    asyncio.run(course_embedding_analysis(course_ref_to_course, cache_dir, logger))

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

