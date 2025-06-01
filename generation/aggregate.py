import asyncio
from collections import Counter
from itertools import combinations
from logging import Logger

import numpy as np
from keybert import KeyBERT
from tqdm.asyncio import tqdm

from course import Course
from embeddings import get_model, get_embedding
from enrollment_data import GradeData
from instructors import FullInstructor


def quick_statistics(course_ref_to_course: dict[Course.Reference, Course], instructors: list[FullInstructor], logger):

    total_courses = len(course_ref_to_course)
    school_cumulative_grades = GradeData.empty()

    total_instructors = len(instructors)

    total_detected_requisites = 0

    for course, course_data in course_ref_to_course.items():
        cumulative_grade_data = course_data.cumulative_grade_data
        if cumulative_grade_data:
            school_cumulative_grades = school_cumulative_grades.merge_with(cumulative_grade_data)

        if course_data.prerequisites:
            total_detected_requisites += len(course_data.prerequisites.course_references)

    total_ratings = 0

    for instructor in instructors:
        if not instructor.rmp_data:
            continue

        rmp_data = instructor.rmp_data
        total_ratings += len(rmp_data.ratings)


    logger.info("Total courses: %d", total_courses)
    logger.info("School cumulative grades: %s", school_cumulative_grades)
    logger.info("Total instructors: %d", total_instructors)
    logger.info("Total detected requisites: %d", total_detected_requisites)
    logger.info("Total ratings: %d", total_ratings)

    return {
        "total_courses": total_courses,
        "total_grades_given": school_cumulative_grades,
        "total_instructors": total_instructors,
        "total_detected_requisites": total_detected_requisites,
        "total_ratings": total_ratings,
    }

def determine_satisfies(course_ref_to_course: dict[Course.Reference, Course]):

    for course in tqdm(course_ref_to_course.values(), desc="Determining Satisfies", unit="course"):
        requisites = course.prerequisites.course_references

        for requisite in requisites:
            if requisite not in course_ref_to_course:
                continue

            requisite_course = course_ref_to_course[requisite]
            requisite_course.satisfies.add(course.course_reference)


def aggregate_cross_listings(course_ref_to_course: dict[Course.Reference, Course], logger: Logger):
    courses = course_ref_to_course.values()
    pair_counter: Counter[tuple[str, str]] = Counter()

    for course in courses:
        subjects = sorted(course.course_reference.subjects)
        for a, b in combinations(subjects, 2):
            pair_counter[(a, b)] += 1

    result: list[dict] = []
    for (a, b), count in pair_counter.items():
        result.append({"s1": a, "s2": b, "value": count})

    logger.info("Aggregated cross-listings for %d pairs", len(result))

    return result


async def course_embedding_analysis(course_ref_to_course: dict[Course.Reference, Course], cache_dir, logger):

    model = get_model(cache_dir, logger)

    async def embed_course(course_ref, course):
        summary = course.get_short_summary()
        # Wrap the synchronous get_embedding call in asyncio.to_thread if necessary.
        embedding = await asyncio.to_thread(get_embedding, cache_dir, model, summary, logger)

        # Update progress safely using the lock.
        return course_ref, embedding

    # Create tasks for all courses.
    tasks = [
        embed_course(course_ref, course)
        for course_ref, course in course_ref_to_course.items()
    ]

    # Await tasks concurrently.
    results = await tqdm.gather(*tasks, position=0, desc="Course Similarity Embedding Analysis", unit="course")

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

async def define_keywords(course_ref_to_course: dict[Course.Reference, Course], cache_dir, logger):
    kw_model = KeyBERT()

    def set_keywords(course: Course):
        description = course.description.strip()

        if not description:
            return

        keywords = kw_model.extract_keywords(
            description,
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=5,
            use_maxsum=True,
            nr_candidates=10,
        )

        actual_keywords = [keyword[0] for keyword in keywords]
        course.keywords = actual_keywords

    tasks = [
        asyncio.to_thread(set_keywords, course)
        for course in course_ref_to_course.values()
    ]

    await tqdm.gather(*tasks, desc="Extracting Keywords", unit="course")

def aggregate_courses(course_ref_to_course: dict[Course.Reference, Course], instructors, cache_dir, logger):
    determine_satisfies(course_ref_to_course)

    aggregated_cross_listings = aggregate_cross_listings(course_ref_to_course, logger)

    explorer_extras = {
        "cross_listings": aggregated_cross_listings,
    }

    qs = quick_statistics(course_ref_to_course, instructors, logger)

    asyncio.run(course_embedding_analysis(course_ref_to_course, cache_dir, logger))
    asyncio.run(define_keywords(course_ref_to_course, cache_dir, logger))

    return qs, explorer_extras

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

