import logging
import os

import coloredlogs
from dotenv import load_dotenv

from cytoscape import build_graphs, cleanup_graphs, generate_styles, generate_style_from_graph
from enrollment import sync_enrollment_terms, build_from_mega_query
from logging_util import get_logging_level
from madgrades import add_madgrades_data
from open_ai import get_openai_client, optimize_prerequisites
from rmp import get_ratings
from save import write_data
from webscrape import get_course_urls, scrape_all, build_subject_to_courses


def main():
    load_dotenv()

    logging_level = os.getenv("LOGGING_LEVEL", None)

    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    max_prerequisites: str = os.getenv("MAX_PREREQUISITES", None)

    madgrades_api_key: str = os.getenv("MADGRADES_API_KEY", None)

    show_api_keys = os.getenv("SHOW_API_KEY", False) == "True"

    data_dir = os.getenv("DATA_DIRECTORY", None)

    warn_missing_madgrades_api_key = madgrades_api_key is None
    if warn_missing_madgrades_api_key:
        raise ValueError("No Madgrades API key set. Please set the MADGRADES_API_KEY environment variable.")

    warn_missing_data_dir = data_dir is None
    if warn_missing_data_dir:
        raise ValueError("No data directory set. Please set the DATA_DIRECTORY environment variable.")

    logger = logging.getLogger(__name__)

    warn_missing_logging_level = logging_level is None
    logging_level = get_logging_level(level_name=logging_level) or logging.INFO
    logger.setLevel(logging_level)
    coloredlogs.install(level=logging_level, logger=logger)

    warn_missing_prerequisites = max_prerequisites is None
    max_prerequisites: int | float = int(max_prerequisites) if max_prerequisites is not None else float("inf")

    if warn_missing_prerequisites:
        logger.warning("No maximum prerequisites set. Defaulting to infinity (no optimization).")
    if warn_missing_logging_level:
        logger.warning("No logging level set. Defaulting to INFO.")

    open_ai_client = get_openai_client(api_key=openai_api_key, logger=logger, show_api_key=show_api_keys)

    stats = {
        "subjects": 0,
        "courses": 0,
        "original_prerequisites": 0,
        "unknown_madgrades_courses": 0,
        "instructors": 0,
        "instructors_with_ratings": 0,
        "prompt_tokens": 0,
        "total_tokens": 0,
        "removed_prerequisites": 0,
    }

    site_map_urls = get_course_urls(logger=logger)
    subject_to_full_subject, course_ref_to_course = scrape_all(urls=site_map_urls, stats=stats, logger=logger)
    terms = add_madgrades_data(
        course_ref_to_course=course_ref_to_course, 
        madgrades_api_key=madgrades_api_key,
        stats=stats, 
        logger=logger
    )

    sync_enrollment_terms(terms=terms, logger=logger)
    latest_term = max(terms.keys())

    instructors = build_from_mega_query(term_code=latest_term, terms=terms, course_ref_to_course=course_ref_to_course, logger=logger)
    instructor_to_rating = get_ratings(instructors=instructors, stats=stats, logger=logger)

    optimize_prerequisites(
        client=open_ai_client,
        model="text-embedding-3-small",
        course_ref_to_course=course_ref_to_course,
        max_prerequisites=max_prerequisites,
        max_runtime=30,
        max_retries=50,
        max_threads=10,
        stats=stats,
        logger=logger
    )

    identifier_to_course = {course.get_identifier(): course for course in course_ref_to_course.values()}
    subject_to_courses = build_subject_to_courses(course_ref_to_course=course_ref_to_course)

    global_graph, subject_to_graph = build_graphs(
        course_ref_to_course=course_ref_to_course,
        subject_to_courses=subject_to_courses,
        logger=logger
    )

    cleanup_graphs(
        global_graph=global_graph,
        subject_to_graph=subject_to_graph,
        logger=logger
    )

    subject_to_style = generate_styles(subject_to_graph=subject_to_graph)
    global_style = generate_style_from_graph(global_graph)

    write_data(
        data_dir=data_dir,
        subject_to_full_subject=subject_to_full_subject,
        subject_to_courses=subject_to_courses,
        identifier_to_course=identifier_to_course,
        global_graph=global_graph,
        subject_to_graph=subject_to_graph,
        global_style=global_style,
        subject_to_style=subject_to_style,
        instructor_to_rating=instructor_to_rating,
        terms=terms,
        stats=stats,
        logger=logger
    )


if __name__ == "__main__":
    main()
