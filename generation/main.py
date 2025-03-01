import asyncio
import logging
from argparse import ArgumentParser
from logging import Logger

import coloredlogs

from cache import write_cache, read_cache
from course import Course
from enrollment import sync_enrollment_terms, build_from_mega_query
from instructors import get_ratings
from madgrades import add_madgrades_data
from open_ai import optimize_prerequisites, get_openai_client
from webscrape import get_course_urls, scrape_all


def generate_parser():
    """
    Build the argument parser for command line arguments.
    """
    parser = ArgumentParser(
        description="Generates course map data for UW-Madison courses.",
    )
    parser.add_argument(
        "data_dir",
        type=str,
        help="Directory to save the generated data.",
        default="data"
    )
    parser.add_argument(
        "-c", "--cache_dir",
        type=str,
        help="Directory to save the cached data.",
        default=".cache"
    )
    parser.add_argument(
        "--openai_key",
        type=str,
        help="OpenAI API key for embeddings.",
        required=True,
    )
    parser.add_argument(
        "--madgrades_key",
        type=str,
        help="Madgrades API key for course data.",
        required=True,
    )
    parser.add_argument(
        "--step",
        choices=["force", "courses", "madgrades", "instructors", "optimize", "madgrades", "graph"],
        help="Strategy for generating course map data.",
        required=True,
    )
    parser.add_argument(
        "--max_prerequisites",
        type=int,
        help="Maximum number of prerequisites to keep for each course.",
        default=3,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    return parser

def filter_step(step_name, allowed_step):
    if step_name == "force":
        return True
    return step_name == allowed_step

def courses(
        logger: Logger
):
    site_map_urls = get_course_urls(logger=logger)
    subject_to_full_subject, course_ref_to_course = scrape_all(urls=site_map_urls, logger=logger)
    return subject_to_full_subject, course_ref_to_course

def madgrades(
        course_ref_to_course,
        madgrades_api_key,
        logger: Logger
):
    terms = asyncio.run(add_madgrades_data(
        course_ref_to_course=course_ref_to_course,
        madgrades_api_key=madgrades_api_key,
        logger=logger
    ))

    sync_enrollment_terms(terms=terms, logger=logger)
    latest_term = max(terms.keys())

    return terms, latest_term

def instructors(
        course_ref_to_course,
        terms,
        logger
):
    instructors_emails = asyncio.run(build_from_mega_query(selected_term=max(terms.keys()), terms=terms, course_ref_to_course=course_ref_to_course, logger=logger))
    instructor_to_rating = asyncio.run(get_ratings(instructors=instructors_emails, logger=logger))
    return instructor_to_rating, instructors_emails

def optimize(
    course_ref_to_course,
    max_prerequisites,
    openai_api_key,
    verbose,
    logger,
):
    open_ai_client = get_openai_client(
        api_key=openai_api_key,
        logger=logger,
        verbose=verbose
    )
    asyncio.run(optimize_prerequisites(
        client=open_ai_client,
        model="text-embedding-3-small",
        course_ref_to_course=course_ref_to_course,
        max_prerequisites=max_prerequisites,
        max_retries=50,
        max_threads=10,
        logger=logger
    ))

def read_course_ref_to_course_cache(cache_data):
    return {Course.Reference.from_string(k): Course.from_json(v) for k, v in cache_data.items()}

def read_terms_cache(cache_data):
    return {int(k): v for k, v in cache_data.items()}

def main():
    parser = generate_parser()
    args = parser.parse_args()

    data_dir = str(args.data_dir)
    cache_dir = str(args.cache_dir)
    openai_api_key = str(args.openai_key)
    madgrades_api_key = str(args.madgrades_key)
    step = str(args.step).lower()
    max_prerequisites = int(args.max_prerequisites)
    verbose = bool(args.verbose)

    logger = logging.getLogger(__name__)
    logging_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(logging_level)
    coloredlogs.install(level=logging_level, logger=logger)

    subject_to_full_subject, course_ref_to_course, terms, latest_term = None, None, None, None
    if filter_step(step, "courses"):
        logger.info("Fetching course data...")
        subject_to_full_subject, course_ref_to_course = courses(logger=logger)

        write_cache(cache_dir, ("courses",), "subject_to_full_subject", subject_to_full_subject, logger)
        write_cache(cache_dir, ("courses",), "course_ref_to_course", course_ref_to_course, logger)
        logger.info("Course data fetched successfully.")

    if filter_step(step, "madgrades"):
        logger.info("Fetching madgrades data...")
        if course_ref_to_course is None:
            course_ref_to_course = read_cache(cache_dir, ("courses",), "course_ref_to_course", logger)
            course_ref_to_course = read_course_ref_to_course_cache(course_ref_to_course)
        terms, latest_term = madgrades(course_ref_to_course=course_ref_to_course, madgrades_api_key=madgrades_api_key, logger=logger)

        write_cache(cache_dir, ("madgrades",), "terms", terms, logger)
        write_cache(cache_dir, ("courses",), "course_ref_to_course", course_ref_to_course, logger)
        logger.info("Madgrades data fetched successfully.")

    if filter_step(step,  "instructors"):
        logger.info("Fetching instructor data...")
        if course_ref_to_course is None:
            course_ref_to_course = read_cache(cache_dir, ("courses",), "course_ref_to_course", logger)
            course_ref_to_course = read_course_ref_to_course_cache(course_ref_to_course)

        if terms is None or latest_term is None:
            terms = read_cache(cache_dir, ("madgrades",), "terms", logger)
            terms = read_terms_cache(terms)

        instructor_to_rating, instructors_emails = instructors(course_ref_to_course=course_ref_to_course, terms=terms, logger=logger)

        write_cache(cache_dir, ("instructors",), "instructor_to_rating", instructor_to_rating, logger)
        write_cache(cache_dir, ("courses",), "course_ref_to_course", course_ref_to_course, logger)
        logger.info("Instructor data fetched successfully.")


    if filter_step(step, "optimize"):
        logger.info("Optimizing course data...")
        if course_ref_to_course is None:
            course_ref_to_course = read_cache(cache_dir, ("courses",), "course_ref_to_course", logger)
            course_ref_to_course = read_course_ref_to_course_cache(course_ref_to_course)

        optimize(
            course_ref_to_course=course_ref_to_course,
            max_prerequisites=max_prerequisites,
            openai_api_key=openai_api_key,
            verbose=verbose,
            logger=logger
        )

        write_cache(cache_dir, ("courses",), "course_ref_to_course", course_ref_to_course, logger)
        logger.info("Course data optimized successfully.")


    # open_ai_client = get_openai_client(
    #     api_key=openai_api_key,
    #     logger=logger,
    #     verbose=verbose
    # )
    #
    #
    # optimize_prerequisites(
    #     client=open_ai_client,
    #     model="text-embedding-3-small",
    #     course_ref_to_course=course_ref_to_course,
    #     max_prerequisites=max_prerequisites,
    #     max_runtime=30,
    #     max_retries=50,
    #     max_threads=10,
    #     stats=stats,
    #     logger=logger
    # )
    #
    # identifier_to_course = {course.get_identifier(): course for course in course_ref_to_course.values()}
    # subject_to_courses = build_subject_to_courses(course_ref_to_course=course_ref_to_course)
    #
    # global_graph, subject_to_graph = build_graphs(
    #     course_ref_to_course=course_ref_to_course,
    #     subject_to_courses=subject_to_courses,
    #     logger=logger
    # )
    #
    # cleanup_graphs(
    #     global_graph=global_graph,
    #     subject_to_graph=subject_to_graph,
    #     logger=logger
    # )
    #
    # subject_to_style = generate_styles(subject_to_graph=subject_to_graph)
    # global_style = generate_style_from_graph(global_graph)

if __name__ == "__main__":
    main()
