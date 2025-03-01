import asyncio
import hashlib
from logging import Logger

import numpy as np
from openai import OpenAI

from course import Course
from cache import read_embedding_cache, write_embedding_cache


def get_openai_client(api_key: str, logger: Logger, verbose: bool):
    """
    Returns an OpenAI client object.
    """
    if api_key is None or api_key == "REPLACE_WITH_OPENAI_API_KEY":
        logger.warning("No OpenAI API key provided.")
        return None
    return OpenAI(api_key=api_key)

def get_embedding(cache_dir, client: OpenAI, model, text, logger):
    sha256 = hashlib.sha256(text.encode()).hexdigest()

    # Check if the embedding already exists
    embedding = read_embedding_cache(cache_dir, sha256, logger)

    if embedding is None:
        response = client.embeddings.create(model=model, input=text)
        embedding = response.data[0].embedding

        logger.debug(f"Embedding for '{text}' not found in cache. Caching it now.")
        write_embedding_cache(cache_dir, sha256, embedding, logger)

    return embedding

def cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_best_prerequisite(cache_dir, client, model, course, prerequisites, max_prerequisites, logger) -> list[Course]:
    course_embedding = get_embedding(cache_dir, client, model, course.get_full_summary(), logger)
    prerequisite_embeddings = [
        (prereq, get_embedding(cache_dir, client, model, prereq.get_short_summary(), logger)) for prereq in prerequisites
    ]

    similarities = [
        (prereq, cosine_similarity(course_embedding, prereq_embedding))
        for prereq, prereq_embedding in prerequisite_embeddings
    ]

    # Find the prerequisite with the highest similarity score
    best_prerequisite = sorted(similarities, key=lambda x: x[1], reverse=True)[:max_prerequisites]

    # Return the course object of the best prerequisite
    return [req[0] for req in best_prerequisite]

def prune_prerequisites(cache_dir, client, model, course: Course, course_ref_to_course, max_prerequisites, logger: Logger):
    if len(course.prerequisites.course_references) <= max_prerequisites:
        logger.debug(f"Skipping optimization for {course.get_identifier()} as it has {len(course.prerequisites.course_references)} prerequisites")
        course.optimized_prerequisites = course.prerequisites
        return

    prerequisites = set()
    for reference in course.prerequisites.course_references:
        if reference not in course_ref_to_course:
            logger.error(f"Prerequisite not found in courses: {reference}")
            continue
        c = course_ref_to_course[reference]
        prerequisites.add(c)

    best = find_best_prerequisite(
        cache_dir=cache_dir,
        client=client,
        model=model,
        course=course,
        prerequisites=prerequisites,
        max_prerequisites=max_prerequisites,
        logger=logger
    )
    logger.debug(f"Selected {([c.get_identifier() for c in best])} as the best prerequisite(s) for {course.get_identifier()} out of {len(prerequisites)} options")
    course.optimized_prerequisites = Course.Prerequisites(
        course_references=[c.course_reference for c in best],
        prerequisites_text=course.prerequisites.prerequisites_text
    )

async def optimize_prerequisite(cache_dir, course, client, model, course_ref_to_course, max_prerequisites, max_retries, logger):
    retries = 0
    while retries < max_retries:
        try:
            prune_prerequisites(cache_dir, client, model, course, course_ref_to_course, max_prerequisites, logger)
            return
        except Exception as e:
            retries += 1
            logger.warning(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
            if retries >= max_retries:
                logger.error(f"Optimization for course {course.get_identifier()} failed completely.")
                return None

async def optimize_prerequisites(
        cache_dir: str,
        client: OpenAI,
        model: str,
        course_ref_to_course: dict[Course.Reference, Course],
        max_prerequisites: int | float,
        max_retries: int,
        max_threads: int,
        logger: Logger
):
    total_courses = len(course_ref_to_course)
    logger.info(f"Optimizing prerequisites for {total_courses} courses...")
    completed_courses = 0
    semaphore = asyncio.Semaphore(max_threads)

    async def optimize_course(course):
        nonlocal completed_courses
        async with semaphore:
            await optimize_prerequisite(cache_dir, course, client, model, course_ref_to_course, max_prerequisites, max_retries, logger)
            completed_courses += 1
            remaining_courses = total_courses - completed_courses
            logger.debug(f"Optimization completed for course {course.get_identifier()}. {remaining_courses} courses remaining. ({(completed_courses * 100 / total_courses):.2f}% complete)")

    # Create tasks for each course and wait for them all to complete.
    tasks = [asyncio.create_task(optimize_course(course)) for course in course_ref_to_course.values()]
    await asyncio.gather(*tasks)
    logger.info("Optimization completed.")
