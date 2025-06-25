import asyncio
import hashlib
import os
import re
from logging import getLogger
from os import environ

import numpy as np
import requests_cache
from sentence_transformers import SentenceTransformer
from torch import cuda
from tqdm.asyncio import tqdm

from cache import read_embedding_cache, write_embedding_cache
from course import Course

logger = getLogger(__name__)

initialized_model = None

def get_model(cache_dir):
    global initialized_model

    if initialized_model:
        logger.info("Model already loaded. Reusing the existing model.")
        return initialized_model

    # Disable HTTP request caching to ensure the model is fetched or initialized correctly.
    with requests_cache.disabled():
        model_cache_dir = os.path.join(cache_dir, "model")

        device = "cpu"

        if cuda.is_available():
            logger.info("CUDA is available. Using GPU for model inference.")
            cuda_device = 0

            selected_cuda_device = environ.get("CUDA_DEVICE", None)
            if selected_cuda_device:
                cuda_device = selected_cuda_device
                logger.info(f"CUDA device selected: {selected_cuda_device}")
            else:
                logger.info(f"No specific CUDA device selected. Using default device {cuda_device}.")

            device = f"cuda:{cuda_device}"

        logger.info("Loading model...")
        model =  SentenceTransformer(
            model_name_or_path="avsolatorio/GIST-large-Embedding-v0",
            cache_folder=model_cache_dir,
            trust_remote_code=True,
            device=device
        )

        initialized_model = model
        return model

def get_embedding(cache_dir, model: SentenceTransformer, text):
    sha256 = hashlib.sha256(text.encode()).hexdigest()

    # Check if the embedding already exists
    embedding = read_embedding_cache(cache_dir, sha256)

    if embedding is None:
        embedding = model.encode(text, show_progress_bar=False)

        logger.debug(f"Embedding for '{text}' not found in cache. Caching it now.")
        write_embedding_cache(cache_dir, sha256, embedding)

    return embedding

def normalize(v):
    return v / np.linalg.norm(v)

def cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def average_embedding(embeddings):
    """
    Computes the average of a list of embeddings.
    """
    if not embeddings:
        return None
    return np.mean(embeddings, axis=0)

def find_best_prerequisite(
    cache_dir,
    model,
    course: Course, prerequisites, max_prerequisites
) -> list[Course]:
    prerequisite_text = course.prerequisites.prerequisites_text
    and_count = len(re.findall(r"\d*and\d*", prerequisite_text))
    max_prerequisites += and_count

    course_embedding = get_embedding(cache_dir, model, course.get_full_summary())
    prerequisite_embeddings = [
        (prereq, get_embedding(cache_dir, model, prereq.get_short_summary())) for prereq in
        prerequisites
    ]

    similarities = [
        (prereq, cosine_similarity(course_embedding, prereq_embedding))
        for prereq, prereq_embedding in prerequisite_embeddings
    ]


    # Find the prerequisite with the highest similarity score
    best_prerequisite = sorted(similarities, key=lambda x: x[1], reverse=True)[:max_prerequisites]

    # Return the course object of the best prerequisite
    return [req[0] for req in best_prerequisite]

def score_branch(
        cache_dir,
        model,
        course: Course,
        course_ref_to_course,
        max_enrollment,
        branch: list[Course.Reference],
        semantic_similarity_weight,
        popularity_weight,
):
    if not branch:
        return 0

    course_embedding = get_embedding(cache_dir, model, course.get_full_summary())
    branch_as_courses = [course_ref_to_course[cr] for cr in branch if cr in course_ref_to_course if cr != course.course_reference]
    if not branch_as_courses:
        return 0
    branch_embeddings = [get_embedding(cache_dir, model, course.get_full_summary()) for course in branch_as_courses]
    branch_embedding = average_embedding(branch_embeddings)

    # Calculate the cosine similarity between the course and the branch
    similarity = cosine_similarity(course_embedding, branch_embedding)

    enrollment_count = 0
    if course.cumulative_grade_data:
        enrollment_count = course.cumulative_grade_data.total

    enrollment_score = enrollment_count / max_enrollment

    score = semantic_similarity_weight * similarity + popularity_weight * enrollment_score
    return score


def prune_prerequisites(
        cache_dir,
        model,
        course: Course,
        course_ref_to_course,
        max_enrollment,
        max_prerequisites,
):

    if len(course.prerequisites.course_references) <= max_prerequisites:
        logger.debug(
            f"Skipping optimization for {course.get_identifier()} as it has {len(course.prerequisites.course_references)} prerequisites")
        course.optimized_prerequisites = course.prerequisites.course_references
        return

    branches = course.prerequisites.abstract_syntax_tree.course_combinations()
    semantic_similarity_weight = 0.5
    popularity_weight = 0.5
    best_score = -1
    best_branch = None
    for branch in branches:
        score = score_branch(
            cache_dir=cache_dir,
            model=model,
            course=course,
            course_ref_to_course=course_ref_to_course,
            max_enrollment=max_enrollment,
            branch=branch,
            semantic_similarity_weight=semantic_similarity_weight,
            popularity_weight=popularity_weight,
        )
        if score > best_score:
            best_score = score
            best_branch = branch

    course.optimized_prerequisites = best_branch

    if best_branch is None:

        original_prerequisites = course.prerequisites

        prerequisites = set()
        for reference in original_prerequisites.course_references:
            if reference not in course_ref_to_course:
                logger.error(f"Prerequisite not found in courses: {reference}")
                continue
            c = course_ref_to_course[reference]
            prerequisites.add(c)

        best = find_best_prerequisite(
            cache_dir=cache_dir,
            model=model,
            course=course,
            prerequisites=prerequisites,
            max_prerequisites=max_prerequisites,
        )

        course.optimized_prerequisites = [c.course_reference for c in best]

def optimize_prerequisite(
        cache_dir,
        course,
        model: SentenceTransformer,
        course_ref_to_course,
        max_enrollment,
        max_prerequisites,
        max_retries,
):
    retries = 0
    while retries < max_retries:
        try:
            prune_prerequisites(cache_dir, model, course, course_ref_to_course, max_enrollment, max_prerequisites)
            return
        except Exception as e:
            retries += 1
            logger.warning(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
            if retries >= max_retries:
                logger.error(f"Optimization for course {course.get_identifier()} failed completely.")
                return


async def optimize_prerequisites(
        cache_dir: str,
        model: SentenceTransformer,
        course_ref_to_course: dict[Course.Reference, Course],
        max_prerequisites: int | float,
        max_retries: int,
):
    total_courses = len(course_ref_to_course)
    logger.info(f"Optimizing prerequisites for {total_courses} courses...")

    max_enrollment = max(
        c.cumulative_grade_data.total
        for c in course_ref_to_course.values()
        if c.cumulative_grade_data
    )

    # Create tasks for each course and wait for them all to complete.
    tasks = [
        asyncio.to_thread(optimize_prerequisite,
            cache_dir,
            course,
            model,
            course_ref_to_course,
            max_enrollment,
            max_prerequisites,
            max_retries,
        ) for course in course_ref_to_course.values()
    ]
    await tqdm.gather(*tasks, desc="Optimizing Prerequisites", unit="course")
    logger.info("Optimization completed.")
