import asyncio
import re
import time
from logging import Logger

import aiohttp
import requests
from bs4 import BeautifulSoup, ResultSet
from tqdm.asyncio import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from course import Course
from timer import get_ms

sitemap_url = "https://guide.wisc.edu/sitemap.xml"


async def get_course_blocks(session, url: str, logger: Logger) -> (str, ResultSet):
    attempts = 5
    for attempt in range(1, attempts + 1):
        try:
            time_start = time.time()
            async with session.get(url) as response:
                content = await response.read()
            soup = BeautifulSoup(content, "html.parser")

            subject_title = soup.find(class_="page-title").get_text(strip=True)
            results = soup.find_all("div", class_="courseblock")

            time_elapsed_ms = get_ms(time_start)
            logger.debug(f"Discovered {len(results)} courses for {subject_title} in {time_elapsed_ms}ms")
            return subject_title, results
        except Exception as e:
            logger.error(f"Attempt {attempt} failed for URL {url}: {e}")
            await asyncio.sleep(1)  # Wait 1 second before retrying
    raise Exception(f"Failed to fetch data from {url} after {attempts} attempts.")


def add_data(subjects, course_ref_course, full_subject, blocks, logger):
    full_subject = re.match(r"(.*)\((.*)\)", full_subject)
    full_name = full_subject.group(1).strip()
    abbreviation = full_subject.group(2).replace(" ", "")

    subjects[abbreviation] = full_name

    for block in blocks:
        course = Course.from_block(block, logger)
        if not course:
            continue
        course_ref_course[course.course_reference] = course


def get_course_urls(logger: Logger) -> set[str]:
    logger.info("Fetching and parsing the course sitemap...")

    response = requests.get(sitemap_url)

    if response.status_code != 200:
        logger.error(f"Failed to fetch sitemap: {response.status_code}")
        return set()

    soup = BeautifulSoup(response.content, "xml")

    # Step 2: Extract guide-related URLs (only those containing '/guide/')
    sitemap_urls = [
        url.text for url in soup.find_all("loc")
        if re.search(r'/courses/.+', url.text)  # Matches /courses/ followed by any character(s)
    ]

    sitemap_urls = set(sitemap_urls)

    count = len(sitemap_urls)
    logger.info(f"Found {count} course URLs in the sitemap")

    return sitemap_urls


async def scrape_all(urls: set[str], logger: Logger):
    logger.info("Building course data...")

    subject_to_full_subject = {}
    course_ref_to_course = {}

    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit=10)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [get_course_blocks(session, url, logger) for url in urls]
        with logging_redirect_tqdm():
            results = await tqdm.gather(*tasks, desc="Departmental Course Scrape", unit="department")
        for full_subject, blocks in results:
            add_data(subject_to_full_subject, course_ref_to_course, full_subject, blocks, logger)

    logger.info(f"Total subjects found: {len(subject_to_full_subject)}")
    logger.info(f"Total courses found: {len(course_ref_to_course)}")

    return subject_to_full_subject, course_ref_to_course

def build_subject_to_courses(course_ref_to_course: dict[Course.Reference, Course]) -> dict[str, set[Course]]:
    subject_to_courses = dict()
    for course in course_ref_to_course.values():
        subject = course.course_reference.subjects

        for s in subject:
            if s not in subject_to_courses:
                subject_to_courses[s] = set()
            subject_to_courses[s].add(course)

    return subject_to_courses
