import asyncio
from logging import getLogger

import aiohttp
import requests
from aiohttp_client_cache import CachedSession
from tqdm.asyncio import tqdm

from aio_cache import get_aio_cache
from course import Course
from enrollment_data import MadgradesData, TermData
from http_utils import get_user_agent

madgrades_api_endpoint = "https://api.madgrades.com/v1/"
page_size = 100

logger = getLogger(__name__)


def get_madgrades_terms(madgrades_api_key) -> dict[int, str]:
    logger.info("Fetching Madgrades terms...")
    headers = {
        "Authorization": f"Token token={madgrades_api_key}",
        "User-Agent": get_user_agent(),
    }
    response = requests.get(url=madgrades_api_endpoint + "terms", headers=headers)
    return {
        int(term_code): term_name for term_code, term_name in response.json().items()
    }


async def process_course(
    session,
    madgrade_course,
    course_ref_to_course,
    madgrades_api_key,
    current_page,
    total_pages,
):
    course_number = madgrade_course["number"]
    subjects = madgrade_course["subjects"]
    subject_set = {subject["abbreviation"].replace(" ", "") for subject in subjects}
    course_ref = Course.Reference(subject_set, course_number)

    if course_ref not in course_ref_to_course:
        logger.debug(f"Unknown course discovered from Madgrades: {course_ref}")
        return

    grades_url = madgrade_course["url"] + "/grades"
    madgrades_data = await MadgradesData.from_madgrades_async(
        session, grades_url, madgrades_api_key, current_page, attempts=10
    )
    course = course_ref_to_course[course_ref]
    course.cumulative_grade_data = madgrades_data.cumulative

    for term, grade_data in madgrades_data.by_term.items():
        term_data = TermData(None, None)
        if course.term_data.get(term):
            term_data = course.term_data[term]

        term_data.grade_data = grade_data
        course.term_data[term] = term_data

    logger.debug(
        f"Adding madgrades data to course {course_ref} of page {current_page}/{total_pages}"
    )


async def fetch_and_process_page(session, url, course_ref_to_course, key, attempts=5):
    async with session.get(
        url,
        headers={"Authorization": f"Token token={key}", "User-Agent": get_user_agent()},
    ) as resp:
        try:
            data = await resp.json()
        except Exception as e:
            if attempts > 0:
                logger.warning(f"Failed to fetch page {url}: {e}. Retrying...")
                await asyncio.sleep(1)
                await fetch_and_process_page(
                    session, url, course_ref_to_course, key, attempts - 1
                )
            else:
                logger.warning(f"Failed to fetch page {url}: {e}")
            return

    current_page = data["currentPage"]
    total_pages = data["totalPages"]

    await tqdm.gather(
        *[
            process_course(
                session, course, course_ref_to_course, key, current_page, total_pages
            )
            for course in data["results"]
        ],
        desc=f"Madgrades Data Worker ({current_page}/{total_pages})",
        unit="course",
    )
    logger.debug(
        f"Courses from  {data['currentPage']}/{data['totalPages']} fully loaded."
    )


async def add_madgrades_data(course_ref_to_course, madgrades_api_key):
    base = madgrades_api_endpoint + "courses"
    params = f"?per_page={page_size}"
    connector = aiohttp.TCPConnector(limit_per_host=10)
    async with CachedSession(cache=get_aio_cache(), connector=connector) as session:
        first_url = base + params
        async with session.get(
            first_url,
            headers={
                "Authorization": f"Token token={madgrades_api_key}",
                "User-Agent": get_user_agent(),
            },
        ) as resp:
            first = await resp.json()
        total = first["totalPages"]
        urls = [f"{base}{params}&page={i}" for i in range(1, total + 1)]
        [
            await fetch_and_process_page(
                session, url, course_ref_to_course, madgrades_api_key
            )
            for url in tqdm(urls, desc="Madgrades Data Worker", unit="page")
        ]
    return get_madgrades_terms(madgrades_api_key)
