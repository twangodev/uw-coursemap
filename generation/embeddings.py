import asyncio
import hashlib
import os
import re
from logging import Logger
from typing import List

import numpy as np
import requests_cache
from keybert.backend import BaseEmbedder
from sentence_transformers import SentenceTransformer
from tqdm.asyncio import tqdm

from cache import read_embedding_cache, write_embedding_cache, write_course_ref_to_course_cache
from course import Course

initialized_model = None

def get_model(cache_dir, logger: Logger):
    # Disable HTTP request caching to ensure the model is fetched or initialized correctly.
    with requests_cache.disabled():
        model_cache_dir = os.path.join(cache_dir, "model")
        model =  SentenceTransformer(
            model_name_or_path="avsolatorio/GIST-large-Embedding-v0",
            cache_folder=model_cache_dir,
            trust_remote_code=True,
        )

        global initialized_model
        if initialized_model is None:
            logger.info("Loading model...")
            initialized_model = model
        else:
            logger.info("Model already loaded. Reusing the existing model.")

        return initialized_model

def get_embedding(cache_dir, model: SentenceTransformer, text, logger):
    sha256 = hashlib.sha256(text.encode()).hexdigest()

    # Check if the embedding already exists
    embedding = read_embedding_cache(cache_dir, sha256, logger)

    if embedding is None:
        embedding = model.encode(text, show_progress_bar=False)

        logger.debug(f"Embedding for '{text}' not found in cache. Caching it now.")
        write_embedding_cache(cache_dir, sha256, embedding, logger)

    return embedding

class CachedBaseEmbedder(BaseEmbedder):

    def __init__(self, cache_dir, model: SentenceTransformer, logger: Logger):
        super().__init__()
        self.cache_dir = cache_dir
        self.model = model
        self.logger = logger


    def embed(self, documents: List[str], verbose: bool = False) -> np.ndarray:
        embeddings =  [get_embedding(self.cache_dir, self.model, text, self.logger) for text in documents]
        return np.vstack(embeddings)



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

def find_best_prerequisite(cache_dir, model, course: Course, prerequisites, max_prerequisites, logger) -> list[Course]:
    prerequisite_text = course.prerequisites.prerequisites_text
    and_count = len(re.findall(r"\d*and\d*", prerequisite_text))
    max_prerequisites += and_count

    course_embedding = get_embedding(cache_dir, model, course.get_full_summary(), logger)
    prerequisite_embeddings = [
        (prereq, get_embedding(cache_dir, model, prereq.get_short_summary(), logger)) for prereq in
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
        logger
):
    if not branch:
        return 0

    course_embedding = get_embedding(cache_dir, model, course.get_full_summary(), logger)
    branch_as_courses = [course_ref_to_course[cr] for cr in branch if cr in course_ref_to_course if cr != course.course_reference]
    if not branch_as_courses:
        return 0
    branch_embeddings = [get_embedding(cache_dir, model, course.get_full_summary(), logger) for course in branch_as_courses]
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
        logger: Logger
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
            logger=logger
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
            logger=logger
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
        logger
):
    retries = 0
    while retries < max_retries:
        try:
            prune_prerequisites(cache_dir, model, course, course_ref_to_course, max_enrollment, max_prerequisites, logger)
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
        logger: Logger
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
            logger
        ) for course in course_ref_to_course.values()
    ]
    await tqdm.gather(*tasks, desc="Optimizing Prerequisites", unit="course")
    logger.info("Optimization completed.")
