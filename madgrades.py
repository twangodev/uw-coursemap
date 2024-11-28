from logging import Logger

import requests

from course import Course, MadgradesData

madgrades_api_endpoint = "https://api.madgrades.com/v1/"

def get_madgrades_terms(madgrades_api_key, logger: Logger) -> dict[int, str]:
    logger.info("Fetching Madgrades terms...")
    auth_header = {"Authorization": f"Token token={madgrades_api_key}" }
    response = requests.get(url=madgrades_api_endpoint + "terms", headers=auth_header)
    return { int(term_code): term_name for term_code, term_name in response.json().items() }

def build_from_pagination(course_ref_to_course, url, madgrades_api_key, stats, logger: Logger):
    if url is None:
        return

    auth_header = {"Authorization": f"Token token={madgrades_api_key}" }
    response = requests.get(url=url, headers=auth_header)
    data = response.json()

    current_page = data["currentPage"]
    total_pages = data["totalPages"]
    results = data["results"]

    logger.info(f"Processing madgrades page {current_page} of {total_pages}...")

    for madgrade_course in results:
        course_number = madgrade_course["number"]
        subjects = madgrade_course["subjects"]

        subject_set = set()
        for subject in subjects:
            abbreviation = subject["abbreviation"]
            parsed_abbr = abbreviation.replace(" ", "")
            subject_set.add(parsed_abbr)

        course_ref = Course.Reference(subject_set, course_number)

        if course_ref not in course_ref_to_course:
            stats["unknown_madgrades_courses"] += 1
            continue

        grades_url = madgrade_course["url"] + "/grades"
        madgrades_data = MadgradesData.from_madgrades(grades_url, madgrades_api_key)

        course = course_ref_to_course[course_ref]
        course.madgrades_data = madgrades_data


    next_page_url = data["nextPageUrl"]
    build_from_pagination(course_ref_to_course, next_page_url, madgrades_api_key, stats, logger)

def add_madgrades_data(course_ref_to_course, madgrades_api_key, stats, logger: Logger):
    terms = get_madgrades_terms(madgrades_api_key, logger)
    build_from_pagination(course_ref_to_course, madgrades_api_endpoint + "courses", madgrades_api_key, stats, logger)

    logger.info(f"Found {stats['unknown_madgrades_courses']} unknown courses in Madgrades that did not match any courses in the course catalog")

    return terms


