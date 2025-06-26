import asyncio
import logging
import os
import socket
import sys
from argparse import ArgumentParser
from logging import getLogger
from os import environ
from os import path

import coloredlogs
import requests_cache
from dotenv import load_dotenv
from tqdm.contrib.logging import logging_redirect_tqdm

from aggregate import aggregate_instructors, aggregate_courses
from aio_cache import set_aio_cache_location, set_aio_cache_expiration
from cache import read_course_ref_to_course_cache, write_course_ref_to_course_cache, \
    write_subject_to_full_subject_cache, write_terms_cache, write_instructors_to_rating_cache, read_terms_cache, \
    write_graphs_cache, read_subject_to_full_subject_cache, read_graphs_cache, read_instructors_to_rating_cache, \
    write_quick_statistics_cache, read_quick_statistics_cache, write_explorer_stats_cache, read_explorer_stats_cache, \
    write_new_terms_cache, write_course_ref_to_meetings_cache, read_course_ref_to_meetings_cache
from cytoscape import build_graphs, cleanup_graphs, generate_styles, generate_style_from_graph
from embeddings import optimize_prerequisites, get_model
from enrollment import sync_enrollment_terms
from instructors import get_ratings, gather_instructor_emails, scrape_rmp_api_key
from madgrades import add_madgrades_data
from save import write_data
from webscrape import get_course_urls, scrape_all, build_subject_to_courses

load_dotenv()

logger = getLogger(__name__)

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


def courses():
    site_map_urls = get_course_urls()
    subject_to_full_subject, course_ref_to_course = asyncio.run(scrape_all(urls=site_map_urls))
    return subject_to_full_subject, course_ref_to_course


def madgrades(
        course_ref_to_course,
        madgrades_api_key,
):
    terms = asyncio.run(add_madgrades_data(
        course_ref_to_course=course_ref_to_course,
        madgrades_api_key=madgrades_api_key,
    ))

    new_terms = sync_enrollment_terms(terms=terms)
    latest_term = max(terms.keys())

    return terms, latest_term, new_terms


def instructors(
        course_ref_to_course,
        terms,
        cache_dir,
):
    api_key = scrape_rmp_api_key()
    instructors_emails, course_ref_to_meetings = asyncio.run(gather_instructor_emails(terms=terms, course_ref_to_course=course_ref_to_course))
    instructor_to_rating = asyncio.run(get_ratings(instructors=instructors_emails, api_key=api_key, course_ref_to_course=course_ref_to_course, cache_dir=cache_dir))
    return instructor_to_rating, instructors_emails, course_ref_to_meetings

def optimize(
        cache_dir,
        course_ref_to_course,
        max_prerequisites,
):
    model = get_model(
        cache_dir=cache_dir,
    )
    asyncio.run(optimize_prerequisites(
        cache_dir=cache_dir,
        model=model,
        course_ref_to_course=course_ref_to_course,
        max_prerequisites=max_prerequisites,
        max_retries=50,
    ))


def graph(
        course_ref_to_course,
        color_map,
):
    subject_to_courses = build_subject_to_courses(course_ref_to_course=course_ref_to_course)

    global_graph, subject_to_graph, course_to_graph = build_graphs(
        course_ref_to_course=course_ref_to_course,
        subject_to_courses=subject_to_courses,
    )

    cleanup_graphs(
        global_graph=global_graph,
        subject_to_graph=subject_to_graph,
        course_to_graph=course_to_graph,
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


old_factory = logging.getLogRecordFactory()
def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.hostname = socket.gethostname()
    return record

logging.setLogRecordFactory(record_factory)

def main():
    parser = generate_parser()
    args = parser.parse_args()

    data_dir = environ.get("DATA_DIR", None)
    if data_dir is None:
        raise_missing_env_var("DATA_DIR")

    cache_dir = str(args.cache_dir)
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists

    cache_expiration = 60 * 60 * 24 * 7 # 1 week

    requests_cache_location = path.join(cache_dir, "requests_cache")
    requests_cache.install_cache(cache_name=requests_cache_location, expires_after=cache_expiration)

    set_aio_cache_location(path.join(cache_dir, "aio_cache"))
    set_aio_cache_expiration(cache_expiration)

    madgrades_api_key = environ.get("MADGRADES_API_KEY", None)

    step = str(args.step).lower()
    max_prerequisites = int(args.max_prerequisites)
    verbose = bool(args.verbose) or env_debug()
    no_build = bool(args.no_build)

    sitemap_base_url = environ.get("SITEMAP_BASE", None)
    if sitemap_base_url is None:
        raise_missing_env_var("SITEMAP_BASE")

    is_a_tty = sys.stdout.isatty()
    is_ci = environ.get("CI", "").strip().lower() == "true"

    show_color = is_a_tty or is_ci

    logging_level = logging.DEBUG if verbose else logging.INFO

    coloredlogs.install(
        level=logging_level,
        isatty=show_color,
        fmt="%(asctime)s.%(msecs)03d %(hostname)s %(name)s[%(process)d] %(levelname)5s %(message)s",
        milliseconds=True,
    )


    with logging_redirect_tqdm():

        if filter_step(step, "courses"):
            logger.info("Fetching course data...")
            subject_to_full_subject, course_ref_to_course = courses()

            write_subject_to_full_subject_cache(cache_dir, subject_to_full_subject)
            write_course_ref_to_course_cache(cache_dir, course_ref_to_course)
            logger.info("Course data fetched successfully.")

        if filter_step(step, "madgrades"):

            if not madgrades_api_key:
                raise_missing_env_var("MADGRADES_API_KEY")

            logger.info("Fetching madgrades data...")
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)
            terms, latest_term, new_terms = madgrades(
                course_ref_to_course=course_ref_to_course,
                madgrades_api_key=madgrades_api_key,
            )

            write_terms_cache(cache_dir, terms)
            write_course_ref_to_course_cache(cache_dir, course_ref_to_course)
            write_new_terms_cache(cache_dir, new_terms)

            logger.info("Madgrades data fetched successfully.")

        if filter_step(step, "instructors"):
            logger.info("Fetching instructor data...")

            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)
            terms = read_terms_cache(cache_dir)

            instructor_to_rating, instructors_emails, course_ref_to_meetings = instructors(
                course_ref_to_course=course_ref_to_course,
                terms=terms,
                cache_dir=cache_dir,
            )

            write_instructors_to_rating_cache(cache_dir, instructor_to_rating)
            write_course_ref_to_meetings_cache(cache_dir, course_ref_to_meetings)
            write_course_ref_to_course_cache(cache_dir, course_ref_to_course)
            course_ref_to_meetings = read_course_ref_to_meetings_cache(cache_dir)
            logger.info("Instructor data fetched successfully.")

        if filter_step(step, "aggregate"):
            logger.info("Aggregating data")

            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)
            instructor_to_rating = read_instructors_to_rating_cache(cache_dir)

            instructor_statistics = aggregate_instructors(
                course_ref_to_course=course_ref_to_course,
                instructor_to_rating=instructor_to_rating,
            )

            instructor_values = instructor_to_rating.values()

            course_statistics, explorer_stats = aggregate_courses(
                course_ref_to_course=course_ref_to_course,
                instructors=instructor_values,
                cache_dir=cache_dir,
            )

            course_statistics = {
                **instructor_statistics,
                **course_statistics,
            }

            write_course_ref_to_course_cache(cache_dir, course_ref_to_course)
            write_instructors_to_rating_cache(cache_dir, instructor_to_rating)

            write_quick_statistics_cache(cache_dir, course_statistics)
            write_explorer_stats_cache(cache_dir, explorer_stats)

            logger.info("Data aggregated successfully.")

        if filter_step(step, "optimize"):
            logger.info("Optimizing course data...")

            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)

            optimize(
                cache_dir=cache_dir,
                course_ref_to_course=course_ref_to_course,
                max_prerequisites=max_prerequisites,
            )

            write_course_ref_to_course_cache(cache_dir, course_ref_to_course)
            logger.info("Course data optimized successfully.")

        if filter_step(step, "graph"):
            logger.info("Building course graph...")

            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)

            color_map = {}
            global_graph, subject_to_graph, course_to_graph, subject_to_style, global_style = graph(
                course_ref_to_course=course_ref_to_course,
                color_map=color_map,
            )

            write_graphs_cache(cache_dir, global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style, color_map)

            logger.info("Course graph built successfully.")

        if not no_build:

            subject_to_full_subject = read_subject_to_full_subject_cache(cache_dir)
            course_ref_to_course = read_course_ref_to_course_cache(cache_dir)

            identifier_to_course = {course.get_identifier(): course for course in course_ref_to_course.values()}

            global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style = read_graphs_cache(cache_dir)

            instructor_to_rating = read_instructors_to_rating_cache(cache_dir)

            terms = read_terms_cache(cache_dir)

            course_statistics = read_quick_statistics_cache(cache_dir)
            explorer_stats = read_explorer_stats_cache(cache_dir)
            course_ref_to_meetings = read_course_ref_to_meetings_cache(cache_dir)

            write_data(
                data_dir=data_dir,
                base_url=sitemap_base_url,
                subject_to_full_subject=subject_to_full_subject,
                identifier_to_course=identifier_to_course,
                global_graph=global_graph,
                subject_to_graph=subject_to_graph,
                course_to_graph=course_to_graph,
                global_style=global_style,
                subject_to_style=subject_to_style,
                instructor_to_rating=instructor_to_rating,
                terms=terms,
                quick_statistics=course_statistics,
                explorer_stats=explorer_stats,
                course_to_meetings=course_ref_to_meetings,
            )


if __name__ == "__main__":
    main()
