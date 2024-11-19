import re
from logging import Logger

import requests
from bs4 import BeautifulSoup, ResultSet

from course import Course


def get_course_blocks(url: str, logger: Logger) -> (str, ResultSet):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    subject_title = soup.find(class_="page-title").get_text(strip=True)

    results = soup.find_all("div", class_="courseblock")
    logger.info(f"Discovered {len(results)} courses for {subject_title}")
    return subject_title, results

def add_data(subjects, course_ref_course, subject_course, full_subject, blocks):
    full_subject = re.match(r"(.*)\((.*)\)", full_subject)
    full_name = full_subject.group(1).strip()
    abbreviation = full_subject.group(2).replace(" ", "")

    subjects[abbreviation] = full_name

    for block in blocks:
        course = Course.from_block(block)
        if not course:
            continue
        course_ref_course[course.course_reference] = course

        for subject in course.course_reference.subjects:
            if subject not in subject_course:
                subject_course[subject] = set()
            subject_course[subject].add(course)

def get_course_urls(sitemap_url: str, logger: Logger) -> list[str]:
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

def scrape_all(urls: list[str], logger: Logger):
    logger.info("Building course data...")

    subject_to_full_subject = dict()
    course_ref_to_course = dict()
    subject_to_courses = dict()

    for url in urls:
        full_subject, blocks = get_course_blocks(url, logger)
        add_data(subject_to_full_subject, course_ref_to_course, subject_to_courses, full_subject, blocks)

    unmatched = set(subject_to_courses.keys()) ^ set(subject_to_full_subject.keys())
    if unmatched:
        logger.warning(f"Unmatched subjects: {unmatched}")

    logger.info(f"Total subjects found: {len(subject_to_full_subject)}")
    logger.info(f"Total courses found: {len(course_ref_to_course)}")
    logger.info(f"Total subject to course mappings: {len(subject_to_courses)}")
    return subject_to_full_subject, course_ref_to_course, subject_to_courses

def build_graphs():
    logger.info("Building course graphs...")

    graph = set()
    subject_graph = dict()

    for subject in subjects_course_map.keys():
        for course in subjects_course_map[subject]:
            if subject not in subject_graph:
                subject_graph[subject] = set()
            course.get_subgraphs(courses, set(), graph, subject_graph[subject])

    return graph, subject_graph
