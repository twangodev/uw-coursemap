import asyncio
import logging
import sys
from argparse import ArgumentParser
from logging import Logger
from os import environ

import coloredlogs
from dotenv import load_dotenv

from aggregate import aggregate_instructors, aggregate_courses
from cache import read_course_ref_to_course_cache, write_course_ref_to_course_cache, \
    write_subject_to_full_subject_cache, write_terms_cache, write_instructors_to_rating_cache, read_terms_cache, \
    write_graphs_cache, read_subject_to_full_subject_cache, read_graphs_cache, read_instructors_to_rating_cache, \
    write_quick_statistics_cache, read_quick_statistics_cache
from cytoscape import build_graphs, cleanup_graphs, generate_styles, generate_style_from_graph
from embeddings import optimize_prerequisites, get_model
from enrollment import sync_enrollment_terms
from instructors import get_ratings, gather_instructor_emails, scrape_rmp_api_key
from madgrades import add_madgrades_data
from save import write_data
from webscrape import get_course_urls, scrape_all, build_subject_to_courses

load_dotenv()

def generate_parser():
    """
    Build the argument parser for command line arguments.
    """
    parser = ArgumentParser(
        description="Generates course map data for UW-Madison courses.",
    )
    parser.add_argument(
        "-c", "--cache_dir",
        type=str,
        help="Directory to save the cached data.",
        default="./.cache"
    )
    parser.add_argument(
        "--step",
        choices=["all", "courses", "madgrades", "instructors", "aggregate", "optimize", "graph"],
        help="Strategy for generating course map data.",
        required=True,
    )
    parser.add_argument(
        "--max_prerequisites",
        type=int,
        help="Maximum number of prerequisites to keep for each course.",
        default=1,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    parser.add_argument(
        "-nb",
        "--no_build",
        action="store_true",
        help="Skips writing the data to the specified directory.",
    )
    return parser


def filter_step(step_name, allowed_step):
    if step_name == "all":
        return True
    return step_name == allowed_step


def courses(
        logger: Logger
):
    site_map_urls = get_course_urls(logger=logger)
    subject_to_full_subject, course_ref_to_course = asyncio.run(scrape_all(urls=site_map_urls, logger=logger))
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
    api_key = scrape_rmp_api_key(logger)
    instructors_emails = asyncio.run(gather_instructor_emails(terms=terms, course_ref_to_course=course_ref_to_course, logger=logger))
    instructor_to_rating = asyncio.run(get_ratings(instructors=instructors_emails, api_key=api_key, course_ref_to_course=course_ref_to_course, logger=logger))
    return instructor_to_rating, instructors_emails

def optimize(
        cache_dir,
        course_ref_to_course,
        max_prerequisites,
        logger,
):
    model = get_model(
        cache_dir=cache_dir,
        logger=logger,
    )
    asyncio.run(optimize_prerequisites(
        cache_dir=cache_dir,
        model=model,
        course_ref_to_course=course_ref_to_course,
        max_prerequisites=max_prerequisites,
        max_retries=50,
        max_threads=10,
        logger=logger
    ))


def graph(
        course_ref_to_course,
        color_map,
        logger
):
    subject_to_courses = build_subject_to_courses(course_ref_to_course=course_ref_to_course)

    global_graph, subject_to_graph, course_to_graph = build_graphs(
        course_ref_to_course=course_ref_to_course,
        subject_to_courses=subject_to_courses,
        logger=logger
    )

    cleanup_graphs(
        global_graph=global_graph,
        subject_to_graph=subject_to_graph,
        course_to_graph=course_to_graph,
        logger=logger
    )

    subject_to_style = generate_styles(subject_to_graph=subject_to_graph, color_map=color_map)
    global_style = generate_style_from_graph(global_graph, color_map)

    return global_graph, subject_to_graph, course_to_graph, subject_to_style, global_style

def raise_missing_env_var(var_name):
    raise ValueError(f"{var_name} environment variable is not set.")

def env_debug() -> bool:
    env_debug_flag = environ.get("DEBUG", None)
    action_debug_flag = environ.get("ACTIONS_RUNNER_DEBUG", None)

    return (env_debug_flag and env_debug_flag.lower() == "true") or \
           (action_debug_flag and action_debug_flag.lower() == "true")

def main():
    parser = generate_parser()
    args = parser.parse_args()

    data_dir = environ.get("DATA_DIR", None)
    if data_dir is None:
        raise_missing_env_var("DATA_DIR")

    cache_dir = str(args.cache_dir)
    madgrades_api_key = environ.get("MADGRADES_API_KEY", None)

    step = str(args.step).lower()
    max_prerequisites = int(args.max_prerequisites)
    verbose = bool(args.verbose) or env_debug()
    no_build = bool(args.no_build)

    logger = logging.getLogger(__name__)
    logging_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(logging_level)

    is_a_tty = sys.stdout.isatty()
    is_ci = environ.get("CI", "").strip().lower() == "true"

    show_color = is_a_tty or is_ci
    coloredlogs.install(level=logging_level, logger=logger, isatty=show_color)

    subject_to_full_subject = None
    course_ref_to_course = None
    terms = None
    global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style = None, None, None, None, None
    instructor_to_rating = None

    if filter_step(step, "courses"):
        logger.info("Fetching course data...")
        subject_to_full_subject, course_ref_to_course = courses(logger=logger)

        write_subject_to_full_subject_cache(cache_dir, subject_to_full_subject, logger=logger)
        write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger)
        logger.info("Course data fetched successfully.")

    if filter_step(step, "madgrades"):

        if not madgrades_api_key:
            raise_missing_env_var("MADGRADES_API_KEY")

        logger.info("Fetching madgrades data...")
        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)
        terms, latest_term = madgrades(course_ref_to_course=course_ref_to_course, madgrades_api_key=madgrades_api_key,
                                       logger=logger)

        write_terms_cache(cache_dir, terms, logger)
        write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger)
        logger.info("Madgrades data fetched successfully.")

    if filter_step(step, "instructors"):
        logger.info("Fetching instructor data...")

        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)

        if terms is None:
            terms = read_terms_cache(cache_dir, logger)

        instructor_to_rating, instructors_emails = instructors(course_ref_to_course=course_ref_to_course, terms=terms,
                                                               logger=logger)

        write_instructors_to_rating_cache(cache_dir, instructor_to_rating, logger)
        write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger)
        logger.info("Instructor data fetched successfully.")

    quick_statistics = None

    if filter_step(step, "aggregate"):
        logger.info("Aggregating data")

        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)

        if instructor_to_rating is None:
            instructor_to_rating = read_instructors_to_rating_cache(cache_dir, logger)

        aggregate_instructors(
            course_ref_to_course=course_ref_to_course,
            instructor_to_rating=instructor_to_rating,
            logger=logger
        )

        quick_statistics = aggregate_courses(
            course_ref_to_course=course_ref_to_course,
            cache_dir=cache_dir,
            logger=logger
        )

        write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger)
        write_instructors_to_rating_cache(cache_dir, instructor_to_rating, logger)
        write_quick_statistics_cache(cache_dir, quick_statistics, logger)

        logger.info("Data aggregated successfully.")

    if filter_step(step, "optimize"):
        logger.info("Optimizing course data...")
        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)

        optimize(
            cache_dir=cache_dir,
            course_ref_to_course=course_ref_to_course,
            max_prerequisites=max_prerequisites,
            logger=logger
        )

        write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger)
        logger.info("Course data optimized successfully.")

    if filter_step(step, "graph"):
        logger.info("Building course graph...")

        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)

        color_map = {}
        global_graph, subject_to_graph, course_to_graph, subject_to_style, global_style = graph(
            course_ref_to_course=course_ref_to_course,
            color_map=color_map,
            logger=logger
        )

        write_graphs_cache(cache_dir, global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style, color_map, logger)

        logger.info("Course graph built successfully.")

    if not no_build:

        if subject_to_full_subject is None:
            subject_to_full_subject = read_subject_to_full_subject_cache(cache_dir, logger)

        if course_ref_to_course is None:
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir, logger)

        subject_to_courses = build_subject_to_courses(course_ref_to_course=course_ref_to_course, )
        identifier_to_course = {course.get_identifier(): course for course in course_ref_to_course.values()}

        graphs = [global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style] 
        if graphs.count(None) >= 1: 
            global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style = read_graphs_cache(cache_dir, logger)

        if instructor_to_rating is None:
            instructor_to_rating = read_instructors_to_rating_cache(cache_dir, logger)

        if terms is None:
            terms = read_terms_cache(cache_dir, logger)

        if quick_statistics is None:
            quick_statistics = read_quick_statistics_cache(cache_dir, logger)

        write_data(
            data_dir=data_dir,
            subject_to_full_subject=subject_to_full_subject,
            subject_to_courses=subject_to_courses,
            identifier_to_course=identifier_to_course,
            global_graph=global_graph,
            subject_to_graph=subject_to_graph,
            course_to_graph=course_to_graph,
            global_style=global_style,
            subject_to_style=subject_to_style,
            instructor_to_rating=instructor_to_rating,
            terms=terms,
            quick_statistics=quick_statistics,
            logger=logger
        )


if __name__ == "__main__":
    main()
