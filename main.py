import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import coloredlogs
from dotenv import load_dotenv
from openai import OpenAI

from cytoscape import build_graphs, cleanup_graphs, generate_styles, generate_style_from_graph
from open_ai import get_openai_client, optimize_prerequisites
from save import write_data
from webscrape import get_course_urls, scrape_all

sitemap_url = "https://guide.wisc.edu/sitemap.xml"


# @app.route('/subjects', methods=['GET'])
# def get_subjects():
#     return jsonify(list(subjects_course_map.keys()))
#
# @app.route('/graph/<subject>', methods=['GET'])
# def get_subject_graph(subject):
#     return jsonify(list(subject_graph_map[subject]))
#
# @app.route('/graph/style/<subject>', methods=['GET'])
# def get_subject_graph_style(subject):
#     return styles[subject]
#
# @app.route('/graphs', methods=['GET'])
# def get_graphs():
#     return jsonify(list(graphs))
#
# @app.route('/graph/style', methods=['GET'])
# def get_graph_styles():
#     return global_style
#
#
#
# def optimize_course(course, courses, max_retries=3, timeout=30):
#     retries = 0
#     while retries < max_retries:
#         try:
#             # Optimize prerequisites (ensure the request doesn't exceed timeout)
#             with ThreadPoolExecutor(max_workers=1) as executor:
#                 future = executor.submit(course.optimize_prerequisites, courses, stats)
#                 return future.result(timeout=timeout)
#         except Exception as e:
#             retries += 1
#             print(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
#             if retries >= max_retries:
#                 print(f"Optimization for course {course.get_identifier()} failed completely.")
#                 return None  # Abandon optimization if all retries fail
#
# def optimize_prerequisitess(courses, client):
#     logger.info("Optimizing prerequisites...")
#
#     # Use ThreadPoolExecutor to handle multiple courses concurrently
#     total_courses = len(courses)
#     completed_courses = 0
#
#     with ThreadPoolExecutor(max_workers=100) as executor:
#         future_to_course = {
#             executor.submit(optimize_course, course, courses): course
#             for course in courses.values()
#         }
#         for future in as_completed(future_to_course):
#             course = future_to_course[future]
#             try:
#                 future.result()  # This will re-raise any exception from the thread
#                 completed_courses += 1
#                 remaining_courses = total_courses - completed_courses
#                 print(f"Optimization completed for course {course.get_identifier()}. {remaining_courses} courses remaining.")
#             except Exception as e:
#                 completed_courses += 1
#                 remaining_courses = total_courses - completed_courses
#                 print(f"Optimization failed for course {course.get_identifier()}: {e}. {remaining_courses} courses remaining.")
#
#     print(f"Prerequisites optimized. Total tokens used: {stats['total_tokens']}. Removed requisites: {stats['removed_requisites']}")
#

#

#

def get_logging_level(level_name):
    if level_name is None:
        return None
    try:
        # Convert level name string to integer level
        return getattr(logging, level_name.upper())
    except AttributeError:
        raise ValueError(f"Invalid logging level: {level_name}")

def main():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    data_dir = os.getenv("DATA_DIRECTORY", None)
    max_prerequisites = os.getenv("MAX_PREREQUISITES", None)
    logging_level = os.getenv("LOGGING_LEVEL", None)
    show_api_key = os.getenv("SHOW_API_KEY", False) == "True"

    warn_missing_data_dir = data_dir is None
    if warn_missing_data_dir:
        raise ValueError("No data directory set. Please set the DATA_DIRECTORY environment variable.")

    warn_missing_max_prerequisites = max_prerequisites is None
    max_prerequisites = int(max_prerequisites) if max_prerequisites is not None else 1

    logger = logging.getLogger(__name__)

    warn_missing_logging_level = logging_level is None
    logging_level = get_logging_level(level_name=logging_level) or logging.INFO
    logger.setLevel(logging_level)
    coloredlogs.install(level=logging_level, logger=logger)

    if warn_missing_max_prerequisites:
        logger.warning("No max prerequisites set. Defaulting to 1")

    if warn_missing_logging_level:
        logger.warning("No logging level set. Defaulting to INFO")

    open_ai_client = get_openai_client(api_key=openai_api_key, logger=logger, show_api_key=show_api_key)

    site_map_urls = get_course_urls(sitemap_url=sitemap_url, logger=logger)
    subject_to_full_subject, course_ref_to_course, subject_to_courses = scrape_all(urls=site_map_urls, logger=logger)
    identifier_to_course = {course.get_identifier(): course for course in course_ref_to_course.values()}

    optimize_prerequisites(
        client=open_ai_client,
        model="text-embedding-3-small",
        course_ref_to_course=course_ref_to_course,
        max_runtime=30,
        max_retries=50,
        max_threads=10,
        logger=logger
    )

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
        logger=logger
    )


if __name__ == "__main__":
    main()