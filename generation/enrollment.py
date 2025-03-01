import asyncio
from json import JSONDecodeError
from logging import Logger

import aiohttp
import requests

from course import Course
from enrollment_data import EnrollmentData

terms_url = "https://public.enroll.wisc.edu/api/search/v1/aggregate"
query_url = "https://public.enroll.wisc.edu/api/search/v1"
enrollment_package_base_url = "https://public.enroll.wisc.edu/api/search/v1/enrollmentPackages"


def build_enrollment_package_base_url(term, subject_code, course_id):
    return f"{enrollment_package_base_url}/{term}/{subject_code}/{course_id}"


def sync_enrollment_terms(terms, logger: Logger):
    logger.info("Fetching latest terms...")

    response = requests.get(url=terms_url)
    data = response.json()

    for term in data["terms"]:
        term_code = int(term["termCode"])

        if term_code in terms:
            logger.debug(f"Skipping duplicate term code: {term_code}")
            continue

        short_description = term["shortDescription"]
        logger.debug(f"Found new term code: {term_code} - {short_description}")
        terms[term_code] = short_description


async def build_from_mega_query(selected_term, terms, course_ref_to_course, logger: Logger):
    post_data = {
        "selectedTerm": selected_term,
        "queryString": "",
        "filters": [],
        "page": 1,
        "pageSize": 1
    }

    async with aiohttp.ClientSession() as session:
        logger.debug("Building enrollment package...")
        async with session.post(url=query_url, json=post_data) as response:
            data = await response.json()
        course_count = data["found"]

        post_data["pageSize"] = course_count
        logger.debug(f"Discovered {course_count} courses in the latest term. Syncing terms...")
        async with session.post(url=query_url, json=post_data) as response:
            data = await response.json()

        hits = data["hits"]
        all_instructors = {}

        # Create tasks for each hit to concurrently fetch enrollment package data.
        tasks = [
            process_hit(hit, i, course_count, selected_term, terms, course_ref_to_course, logger, session)
            for i, hit in enumerate(hits)
        ]
        results = await asyncio.gather(*tasks)
        for instructors in results:
            if instructors is None:
                continue
            for full_name, email in instructors.items():
                all_instructors.setdefault(full_name, email)

        logger.info(f"Discovered {len(all_instructors)} unique instructors teaching in the latest term")
        return all_instructors


async def process_hit(hit, i, course_count, selected_term, terms, course_ref_to_course, logger, session, attempts=10):
    course_code = int(hit["catalogNumber"])
    if len(hit["allCrossListedSubjects"]) > 1:
        enrollment_subjects = hit["allCrossListedSubjects"]
    else:
        enrollment_subjects = [hit["subject"]]

    subjects = {subject["shortDescription"].replace(" ", "") for subject in enrollment_subjects}
    course_ref = Course.Reference(subjects, course_code)

    if course_ref not in course_ref_to_course:
        logger.info(f"Skipping unknown course: {course_ref}")
        return None

    logger.debug(f"Processing course: {course_ref} ({i + 1}/{course_count})")
    course = course_ref_to_course[course_ref]
    enrollment_data = EnrollmentData.from_enrollment(hit, terms)

    subject_code = hit["subject"]["subjectCode"]
    course_id = hit["courseId"]
    enrollment_package_url = build_enrollment_package_base_url(selected_term, subject_code, course_id)

    try:
        async with session.get(url=enrollment_package_url) as response:
            data = await response.json()
    except (JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to fetch enrollment data for {course_ref.get_identifier()}: {str(e)}")
        if attempts > 0:
            logger.info(f"Retrying {attempts} more times...")
            await asyncio.sleep(1)
            return await process_hit(hit, i, course_count, selected_term, terms, course_ref_to_course, logger, session,
                                     attempts - 1)
        return None

    course_instructors = {}
    section_count = len(data)
    logger.debug(f"Found {section_count} sections for {course_ref.get_identifier()}")
    for section in data:
        sections = section.get("sections", [])
        for s in sections:
            section_instructors = s.get("instructors", [])
            for instructor in section_instructors:
                name = instructor["name"]
                first = name["first"]
                last = name["last"]
                full_name = f"{first} {last}"
                email = instructor["email"]
                course_instructors.setdefault(full_name, email)

    enrollment_data.instructors = course_instructors
    logger.debug(f"Added {len(course_instructors)} instructors to {course_ref.get_identifier()}")
    course.enrollment_data = enrollment_data

    return course_instructors
