import re
import time
from logging import Logger

import requests
from bs4 import BeautifulSoup, ResultSet

from course import Course
from timer import get_ms

sitemap_url = "https://guide.wisc.edu/sitemap.xml"

def get_course_blocks(url: str, logger: Logger) -> (str, ResultSet):
    time_start = time.time()
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    subject_title = soup.find(class_="page-title").get_text(strip=True)

    results = soup.find_all("div", class_="courseblock")
    time_elapsed_ms = get_ms(time_start)
    logger.info(f"Discovered {len(results)} courses for {subject_title} in {time_elapsed_ms}")
    return subject_title, results

def add_data(subjects, course_ref_course, full_subject, blocks, stats):
    full_subject = re.match(r"(.*)\((.*)\)", full_subject)
    full_name = full_subject.group(1).strip()
    abbreviation = full_subject.group(2).replace(" ", "")

    subjects[abbreviation] = full_name

    for block in blocks:
        course = Course.from_block(block, stats)
        if not course:
            continue
        course_ref_course[course.course_reference] = course

def get_course_urls(logger: Logger) -> list[str]:
    logger.info("Fetching and parsing the sitemap...")

    response = requests.get(sitemap_url)

    if response.status_code != 200:
        logger.error(f"Failed to fetch sitemap: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "xml")

    # Step 2: Extract guide-related URLs (only those containing '/guide/')
    site_map_urls = [
        url.text for url in soup.find_all("loc")
        if re.search(r'/courses/.+', url.text)  # Matches /courses/ followed by any character(s)
    ]

    count = len(site_map_urls)
    logger.info(f"Found {count} course URLs in the sitemap")

    return site_map_urls

def scrape_all(urls: list[str], stats, logger: Logger):
    logger.info("Building course data...")

    subject_to_full_subject = dict()
    course_ref_to_course = dict()

    for url in urls:
        full_subject, blocks = get_course_blocks(url, logger)
        add_data(subject_to_full_subject, course_ref_to_course, full_subject, blocks, stats)

    logger.info(f"Total subjects found: {len(subject_to_full_subject)}")
    logger.info(f"Total courses found: {len(course_ref_to_course)}")

    stats["subjects"] = len(subject_to_full_subject)
    stats["courses"] = len(course_ref_to_course)

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