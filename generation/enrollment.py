import asyncio
from datetime import timedelta, datetime
from json import JSONDecodeError
from logging import getLogger

import requests
from aiohttp_client_cache import CachedSession
from tqdm.asyncio import tqdm

from aio_cache import get_aio_cache
from course import Course
from enrollment_data import EnrollmentData, TermData

terms_url = "https://public.enroll.wisc.edu/api/search/v1/aggregate"
query_url = "https://public.enroll.wisc.edu/api/search/v1"
enrollment_package_base_url = "https://public.enroll.wisc.edu/api/search/v1/enrollmentPackages"

logger = getLogger(__name__)


def build_enrollment_package_base_url(term, subject_code, course_id):
    return f"{enrollment_package_base_url}/{term}/{subject_code}/{course_id}"


def sync_enrollment_terms(terms):
    term_times = {}

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

        start_date = int(term["instructionBeginDate"])
        end_date = int(term["instructionEndDate"])

        term_times[term_code] = (start_date, end_date)

    return term_times


async def build_from_mega_query(selected_term: str, term_name, terms, course_ref_to_course):
    post_data = {
        "selectedTerm": selected_term,
        "queryString": "",
        "filters": [],
        "page": 1,
        "pageSize": 1
    }

    async with CachedSession(cache=get_aio_cache()) as session:
        logger.debug(f"Building enrollment package for {term_name}...")
        async with session.post(url=query_url, json=post_data) as response:
            data = await response.json()
        course_count = data["found"]

        if not course_count:
            logger.warning(f"No courses found in the {term_name} term")
            return {}

        post_data["pageSize"] = course_count
        logger.debug(f"Discovered {course_count} courses in the {term_name} term. Syncing terms...")
        async with session.post(url=query_url, json=post_data) as response:
            data = await response.json()

        hits = data["hits"]
        all_instructors = {}
        all_meetings = {}

        # Create tasks for each hit to concurrently fetch enrollment package data.
        tasks = [
            process_hit(hit, i, course_count, selected_term, term_name, terms, course_ref_to_course, session)
            for i, hit in enumerate(hits)
        ]
        results = await tqdm.gather(*tasks, desc=f"Courses in {term_name}", unit="course")
        for result in results:
            if result is None:
                continue
            instructors, meetings, course_ref = result
            for full_name, email in instructors.items():
                all_instructors.setdefault(full_name, email)
            
            # Group meetings by course identifier using the course_reference
            if meetings:
                course_identifier = course_ref.get_identifier()
                all_meetings.setdefault(course_identifier, []).extend(meetings)

        logger.info(f"Discovered {len(all_instructors)} unique instructors teaching in {term_name}")
        logger.info(f"Discovered meetings for {len(all_meetings)} courses in {term_name}")
        return all_instructors, all_meetings

def generate_recurring_meetings(start_date_epoch_ms, end_date_epoch_ms, epoch_start_time_ms, epoch_end_time_ms, days_of_week):
    """
    Generate individual start and end times for recurring meetings.

    Args:
        start_date_epoch_ms: Start date for recurrence (full epoch timestamp)
        end_date_epoch_ms: End date for recurrence (full epoch timestamp)
        epoch_start_time_ms: Meeting start time within day (epoch ms representing time of day)
        epoch_end_time_ms: Meeting end time within day (epoch ms representing time of day)
        days_of_week: List of days as strings (e.g., ["MONDAY", "WEDNESDAY", "FRIDAY"])

    Returns:
        List of tuples containing (start_time_ms, end_time_ms) for each occurrence
    """

    if not epoch_start_time_ms or not epoch_end_time_ms:
        return []

    # Map day names to weekday numbers (Monday=0, Sunday=6)
    day_mapping = {
        "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
        "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
    }

    # Convert day names to weekday numbers
    target_weekdays = [day_mapping[day.upper()] for day in days_of_week]

    # Convert dates to datetime objects
    start_date = datetime.fromtimestamp(start_date_epoch_ms / 1000).date()
    end_date = datetime.fromtimestamp(end_date_epoch_ms / 1000).date()

    # Extract time components from epoch times (assuming they represent time of day)
    start_time_dt = datetime.fromtimestamp(epoch_start_time_ms / 1000).time()
    end_time_dt = datetime.fromtimestamp(epoch_end_time_ms / 1000).time()

    meetings = []
    current_date = start_date

    # Iterate through each day from start to end date
    while current_date <= end_date:
        # Check if current day is one of our target weekdays
        if current_date.weekday() in target_weekdays:
            # Combine date with start/end times
            meeting_start_datetime = datetime.combine(current_date, start_time_dt)
            meeting_end_datetime = datetime.combine(current_date, end_time_dt)

            # Convert back to epoch milliseconds
            meeting_start_ms = int(meeting_start_datetime.timestamp() * 1000)
            meeting_end_ms = int(meeting_end_datetime.timestamp() * 1000)

            meetings.append((meeting_start_ms, meeting_end_ms))

        # Move to next day
        current_date += timedelta(days=1)

    return meetings


async def process_hit(hit, i, course_count, selected_term: str, term_name: str, terms, course_ref_to_course, session, attempts=10):
    course_code = int(hit["catalogNumber"])
    if len(hit["allCrossListedSubjects"]) > 1:
        enrollment_subjects = hit["allCrossListedSubjects"]
    else:
        enrollment_subjects = [hit["subject"]]

    subjects = {subject["shortDescription"].replace(" ", "") for subject in enrollment_subjects}
    course_ref = Course.Reference(subjects, course_code)

    if course_ref not in course_ref_to_course:
        logger.debug(f"Skipping unknown course: {course_ref}")
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
            return await process_hit(hit, i, course_count, selected_term, term_name, terms, course_ref_to_course, session,
                                     attempts - 1)
        return None

    course_instructors = {}
    course_meetings = []
    section_count = len(data)

    logger.debug(f"Found {section_count} sections for {course_ref.get_identifier()}")

    for section in data:
        sections = section.get("sections", [])
        for s in sections:

            section_type = s["type"]
            section_number = s["sectionNumber"]
            section_identifier = f"{section_type} {section_number}"

            start_date = s["startDate"]
            end_date = s["endDate"]

            # Get enrollment data for this section
            enrollment_status = s.get("enrollmentStatus", {})
            current_enrollment = enrollment_status.get("currentlyEnrolled", 0)
            capacity = enrollment_status.get("capacity", 0)

            class_meetings = s.get("classMeetings", [])
            for meeting in class_meetings:
                days = meeting["meetingDaysList"]
                meeting_type = meeting["meetingType"]

                start_time = meeting["meetingTimeStart"]
                end_time = meeting["meetingTimeEnd"]

                date = meeting.get("examDate")
                if not days and date: # Not a recurring meeting
                    start_date_time = date + start_time
                    end_date_time = date + end_time
                    course_meeting = EnrollmentData.Meeting(
                        start_time=start_date_time,
                        end_time=end_date_time,
                        type=meeting_type,
                        location=None,  # No location for single meetings
                        name=f"{course.course_reference} {meeting_type}",
                        current_enrollment=current_enrollment
                    )
                    course_meetings.append(course_meeting)
                    continue

                all_meeting_occurrences = generate_recurring_meetings(
                    start_date_epoch_ms=start_date,
                    end_date_epoch_ms=end_date,
                    epoch_start_time_ms=start_time,
                    epoch_end_time_ms=end_time,
                    days_of_week=days
                )

                location = None
                building = meeting.get("building")
                if building:
                    building_name = building["buildingName"]
                    coordinates = (building.get("latitude"), building.get("longitude"))
                    room = meeting.get("room", "No Assigned Room")

                    location = EnrollmentData.MeetingLocation.get_or_create_with_capacity(
                        building=building_name,
                        room=room,
                        coordinates=coordinates,
                        class_capacity=capacity
                    )

                for index, (start, end) in enumerate(all_meeting_occurrences, start=1):
                    name = f"{course.course_reference} - {section_identifier} #{index}"
                    course_meeting = EnrollmentData.Meeting(
                        start_time=start,
                        end_time=end,
                        type=meeting_type,
                        location=location,
                        name=name,
                        current_enrollment=current_enrollment
                    )

                    course_meetings.append(course_meeting)


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

    term_data = TermData(None, None)
    if course.term_data.get(selected_term):
        term_data = course.term_data[selected_term]

    term_data.enrollment_data = enrollment_data

    course.term_data[selected_term] = term_data
    
    # Set has_meetings field based on whether course has meeting data
    course.has_meetings = len(course_meetings) > 0

    return course_instructors, course_meetings, course_ref
