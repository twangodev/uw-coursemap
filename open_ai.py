from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import cache
from logging import Logger
from typing import List, Any

import numpy as np
from openai import OpenAI

from course import Course


def get_openai_client(api_key: str, logger: Logger, show_api_key: bool):
    """
    Returns an OpenAI client object.
    """
    if api_key is None or api_key == "REPLACE_WITH_OPENAI_API_KEY":
        logger.warning("No OpenAI API key provided.")
        return None
    logger.info("Creating OpenAI client" + (f" with API key {api_key}" if show_api_key else ""))
    return OpenAI(api_key=api_key)



def get_embedding(client: OpenAI, model, text, stats):
    response = client.embeddings.create(model=model, input=text)

    stats["prompt_tokens"] += response.usage.prompt_tokens
    stats["total_tokens"] += response.usage.total_tokens
    return response.data[0].embedding

def cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_best_prerequisite(client, model, course, prerequisites, max_prerequisites, stats) -> list[Course]:
    course_embedding = get_embedding(client, model, course.get_full_summary(), stats)
    prerequisite_embeddings = [
        (prereq, get_embedding(client, model, prereq.get_short_summary(), stats)) for prereq in prerequisites
    ]

    similarities = [
        (prereq, cosine_similarity(course_embedding, prereq_embedding))
        for prereq, prereq_embedding in prerequisite_embeddings
    ]

    # Find the prerequisite with the highest similarity score
    best_prerequisite = sorted(similarities, key=lambda x: x[1], reverse=True)[:max_prerequisites]

    # Return the course object of the best prerequisite
    return [req[0] for req in best_prerequisite]

def prune_prerequisites(client, model, course: Course, course_ref_to_course, max_prerequisites, stats, logger: Logger):
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
        client=client,
        model=model,
        course=course,
        prerequisites=prerequisites,
        max_prerequisites=max_prerequisites,
        stats=stats
    )
    logger.debug(f"Selected {([c.get_identifier() for c in best])} as the best prerequisite(s) for {course.get_identifier()} out of {len(prerequisites)} options")
    stats["removed_prerequisites"] += len(prerequisites) - max_prerequisites
    course.optimized_prerequisites = Course.Prerequisites(
        course_references=[c.course_reference for c in best],
        prerequisites_text=course.prerequisites.prerequisites_text
    )

def optimize_prerequisite_thread(client, model, course, course_ref_to_course, max_prerequisites, max_runtime, max_retries, stats, logger):
    retries = 0
    while retries < max_retries:
        try:
            # Optimize prerequisites (ensure the request doesn't exceed timeout)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(prune_prerequisites, client, model, course, course_ref_to_course, max_prerequisites, stats, logger)
                return future.result(timeout=max_runtime)
        except Exception as e:
            retries += 1
            print(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
            if retries >= max_retries:
                print(f"Optimization for course {course.get_identifier()} failed completely.")
                return None  # Abandon optimization if all retries fail

def optimize_prerequisites(
        client: OpenAI,
        model: str,
        course_ref_to_course: dict[Course.Reference, Course],
        max_prerequisites: int | float,
        max_runtime: int,
        max_retries: int,
        max_threads: int,
        stats: dict[str, Any],
        logger: Logger
):
    logger.info("Optimizing prerequisites...")

    # Use ThreadPoolExecutor to handle multiple courses concurrently
    total_courses = len(course_ref_to_course)
    completed_courses = 0

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_course = {
            executor.submit(optimize_prerequisite_thread, client, model, course, course_ref_to_course, max_prerequisites, max_runtime, max_retries, stats, logger): course
            for course in course_ref_to_course.values()
        }
        for future in as_completed(future_to_course):
            course = future_to_course[future]
            completed_courses += 1
            remaining_courses = total_courses - completed_courses
            suffix = f"for course {course.get_identifier()}. {remaining_courses} courses remaining. ({(completed_courses * 100/total_courses):.2f}% complete)"
            try:
                future.result()  # This will re-raise any exception from the thread
                logger.info(f"Optimization completed {suffix}")
            except Exception as e:
                logger.error(f"Optimization failed {suffix}: {e}")

    logger.info(f"Optimization completed. Prompt Tokens used: {stats['prompt_tokens']}. Total tokens used: {stats['total_tokens']}. Removed requisites: {stats['removed_prerequisites']}")
