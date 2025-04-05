import asyncio
from logging import Logger

import aiohttp
import requests
from requests import JSONDecodeError

from course import Course
from enrollment_data import MadgradesData, EnrollmentData, TermData
from json_serializable import JsonSerializable

madgrades_api_endpoint = "https://api.madgrades.com/v1/"
page_size = 100




def get_madgrades_terms(madgrades_api_key, logger: Logger) -> dict[int, str]:
    logger.info("Fetching Madgrades terms...")
    auth_header = {"Authorization": f"Token token={madgrades_api_key}"}
    response = requests.get(url=madgrades_api_endpoint + "terms", headers=auth_header)
    return {int(term_code): term_name for term_code, term_name in response.json().items()}


async def process_course(session, madgrade_course, course_ref_to_course, madgrades_api_key, logger, current_page,
                         total_pages):
    course_number = madgrade_course["number"]
    subjects = madgrade_course["subjects"]
    subject_set = {subject["abbreviation"].replace(" ", "") for subject in subjects}
    course_ref = Course.Reference(subject_set, course_number)

    if course_ref not in course_ref_to_course:
        logger.debug(f"Unknown course discovered from Madgrades: {course_ref}")
        return

    grades_url = madgrade_course["url"] + "/grades"
    madgrades_data = await MadgradesData.from_madgrades_async(session, grades_url, madgrades_api_key, logger, attempts=10)
    course = course_ref_to_course[course_ref]
    course.cumulative_grade_data = madgrades_data.cumulative

    for term, grade_data in madgrades_data.by_term.items():
        term_data = TermData(None, None)
        if course.term_data.get(term):
            term_data = course.term_data[term]

        term_data.grade_data = grade_data
        course.term_data[term] = term_data

    logger.debug(f"Adding madgrades data to course {course_ref} of page {current_page}/{total_pages}")


async def build_from_pagination_async(course_ref_to_course, url, madgrades_api_key, logger, session=None):
    if url is None:
        return

    logger.debug(f"Fetching madgrades data from {url}")

    auth_header = {"Authorization": f"Token token={madgrades_api_key}"}
    if session is None:
        session = aiohttp.ClientSession()

    async with session.get(url, headers=auth_header) as response:
        data = await response.json()

    current_page = data["currentPage"]
    total_pages = data["totalPages"]
    results = data["results"]

    logger.debug(f"Discovered {len(results)} courses in page {current_page}/{total_pages}")

    tasks = []
    for madgrade_course in results:
        tasks.append(
            process_course(session, madgrade_course, course_ref_to_course, madgrades_api_key, logger, current_page,
                           total_pages))

    # Run tasks concurrently
    await asyncio.gather(*tasks)

    # Recursively handle pagination if there's a next page
    next_page_url = data.get("nextPageUrl")
    if next_page_url:
        await build_from_pagination_async(course_ref_to_course, next_page_url, madgrades_api_key, logger, session)
    else:
        await session.close()


async def add_madgrades_data(course_ref_to_course, madgrades_api_key, logger: Logger):
    terms = get_madgrades_terms(madgrades_api_key, logger)
    await build_from_pagination_async(course_ref_to_course,
                                      madgrades_api_endpoint + "courses" + "?per_page=" + str(page_size),
                                      madgrades_api_key, logger)

    return terms
