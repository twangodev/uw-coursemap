import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import coloredlogs
from dotenv import load_dotenv

from open_ai import get_openai_client
from webscrape import get_course_urls, scrape_all

sitemap_url = "https://guide.wisc.edu/sitemap.xml"

logger = logging.getLogger(__name__)

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


def optimize_course(course, courses, stats, max_retries=3, timeout=30):
    retries = 0
    while retries < max_retries:
        try:
            # Optimize prerequisites (ensure the request doesn't exceed timeout)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(course.optimize_prerequisites, courses, stats)
                return future.result(timeout=timeout)
        except Exception as e:
            retries += 1
            print(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
            if retries >= max_retries:
                print(f"Optimization for course {course.get_identifier()} failed completely.")
                return None  # Abandon optimization if all retries fail

def optimize_prerequisites(courses, client, stats):
    logger.info("Optimizing prerequisites...")

    # Use ThreadPoolExecutor to handle multiple courses concurrently
    total_courses = len(courses)
    completed_courses = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_course = {
            executor.submit(optimize_course, course, courses, stats): course
            for course in courses.values()
        }
        for future in as_completed(future_to_course):
            course = future_to_course[future]
            try:
                future.result()  # This will re-raise any exception from the thread
                completed_courses += 1
                remaining_courses = total_courses - completed_courses
                print(f"Optimization completed for course {course.get_identifier()}. {remaining_courses} courses remaining.")
            except Exception as e:
                completed_courses += 1
                remaining_courses = total_courses - completed_courses
                print(f"Optimization failed for course {course.get_identifier()}: {e}. {remaining_courses} courses remaining.")

    print(f"Prerequisites optimized. Total tokens used: {stats['total_tokens']}. Removed requisites: {stats['removed_requisites']}")

# def cleanup_graphs():
#     count = 0
#     if None in graphs:
#         count += 1
#     graphs.discard(None)
#     for subject in subject_graph_map:
#         if None in subject_graph_map[subject]:
#             count += 1
#         subject_graph_map[subject].discard(None)
#     print(f"Removed {count} None graphs")
#
# def generate_style(parent, color):
#     return { parent : color }
#
# def generate_style_from_graph(graph):
#     parents = set()
#     for el in graph:
#         if "data" in el:
#             data = el["data"]
#             if "parent" in data:
#                 parents.add(data["parent"])
#
#     colors = generate_random_hex_colors(len(set(parents)))
#
#     return [generate_style(parent, color) for parent, color in zip(set(parents), colors)]
#
# def generate_styles():
#     return { subject: generate_style_from_graph(subject_graph_map[subject]) for subject in subject_graph_map }
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
    max_prerequisites = os.getenv("MAX_PREREQUISITES", None)
    logging_level = os.getenv("LOGGING_LEVEL", None)
    show_api_key = os.getenv("SHOW_API_KEY", False) == "True"

    warn_missing_max_prerequisites = max_prerequisites is None
    max_prerequisites = int(max_prerequisites) if max_prerequisites is not None else 1

    warn_missing_logging_level = logging_level is None
    logging_level = get_logging_level(level_name=logging_level) or logging.INFO
    logging.basicConfig(level=logging_level)
    coloredlogs.install(level=logging_level, logger=logger)

    if warn_missing_max_prerequisites:
        logger.warning("No max prerequisites set. Defaulting to 1")

    if warn_missing_logging_level:
        logger.warning("No logging level set. Defaulting to INFO")

    open_ai_client = get_openai_client(api_key=openai_api_key, logger=logger, show_api_key=show_api_key)

    site_map_urls = get_course_urls(sitemap_url=sitemap_url, logger=logger)
    subject_to_full_subject, course_ref_to_course, subject_to_courses = scrape_all(urls=site_map_urls, logger=logger)

    identifier_map = {course.get_identifier(): course for course in course_ref_to_course.values()}

    optimize_prerequisites(course_ref_to_course, open_ai_client)

    graphs, subject_graph_map = build_graphs()

    # cleanup_graphs()
    #
    # styles = generate_styles()
    # global_style = generate_style_from_graph(graphs)
    #
    # app.run(debug=False)


if __name__ == "__main__":
    main()