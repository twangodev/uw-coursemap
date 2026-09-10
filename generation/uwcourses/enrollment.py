from datetime import datetime, timedelta, timezone
from logging import getLogger
from zoneinfo import ZoneInfo


from uwcourses.course import Course
from uwcourses.enrollment_data import EnrollmentData, TermData


logger = getLogger(__name__)

# Module-level constants to avoid repeated instantiation
CHICAGO_TZ = ZoneInfo("America/Chicago")
CST_TZ = timezone(timedelta(hours=-6))
DAY_MAPPING = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def extract_time_as_cst_wall_clock(epoch_ms):
    """Extract time from epoch assuming CST encoding of wall clock time.

    The API encodes wall clock times using CST offset year-round,
    so we decode with the same offset to get the correct local time.
    """
    return datetime.fromtimestamp(epoch_ms / 1000, tz=CST_TZ).time()


def convert_single_meeting(
    meeting_date,
    epoch_start_time_ms,
    epoch_end_time_ms,
):
    """
    Convert a single meeting/exam with proper timezone handling.

    Args:
        meeting_date: Date object for the meeting
        epoch_start_time_ms: Meeting start time within day (epoch ms representing time of day)
        epoch_end_time_ms: Meeting end time within day (epoch ms representing time of day)

    Returns:
        Tuple containing (start_time_ms, end_time_ms)
    """
    if epoch_start_time_ms is None or epoch_end_time_ms is None:
        return None

    # Extract time components from API's CST-encoded epochs
    start_time_dt = extract_time_as_cst_wall_clock(epoch_start_time_ms)
    end_time_dt = extract_time_as_cst_wall_clock(epoch_end_time_ms)

    # Combine date with time using Chicago timezone
    meeting_start_datetime = datetime.combine(
        meeting_date, start_time_dt, tzinfo=CHICAGO_TZ
    )
    meeting_end_datetime = datetime.combine(
        meeting_date, end_time_dt, tzinfo=CHICAGO_TZ
    )

    # Convert to epoch milliseconds (handles DST automatically)
    meeting_start_ms = int(meeting_start_datetime.timestamp() * 1000)
    meeting_end_ms = int(meeting_end_datetime.timestamp() * 1000)

    return meeting_start_ms, meeting_end_ms


def generate_recurring_meetings(
    start_date_epoch_ms,
    end_date_epoch_ms,
    epoch_start_time_ms,
    epoch_end_time_ms,
    days_of_week,
):
    """
    Generate individual start and end times for recurring meetings.

    Args:
        start_date_epoch_ms: Start date for recurrence (full epoch timestamp)
        end_date_epoch_ms: End date for recurrence (full epoch timestamp)
        epoch_start_time_ms: Meeting start time within day (epoch ms representing time of day in UTC)
        epoch_end_time_ms: Meeting end time within day (epoch ms representing time of day in UTC)
        days_of_week: List of days as strings (e.g., ["MONDAY", "WEDNESDAY", "FRIDAY"])

    Returns:
        List of tuples containing (start_time_ms, end_time_ms) for each occurrence
    """

    if epoch_start_time_ms is None or epoch_end_time_ms is None:
        return []

    # Convert day names to weekday numbers using module-level constant
    target_weekdays = [DAY_MAPPING[day.upper()] for day in days_of_week]

    # Convert dates using Chicago timezone
    start_date = datetime.fromtimestamp(
        start_date_epoch_ms / 1000, tz=CHICAGO_TZ
    ).date()
    end_date = datetime.fromtimestamp(end_date_epoch_ms / 1000, tz=CHICAGO_TZ).date()

    meetings = []
    current_date = start_date

    # Iterate through each day from start to end date
    while current_date <= end_date:
        # Check if current day is one of our target weekdays
        if current_date.weekday() in target_weekdays:
            # Use the single meeting converter for consistent timezone handling
            meeting_times = convert_single_meeting(
                meeting_date=current_date,
                epoch_start_time_ms=epoch_start_time_ms,
                epoch_end_time_ms=epoch_end_time_ms,
            )

            if meeting_times:
                meetings.append(meeting_times)

        # Move to next day
        current_date += timedelta(days=1)

    return meetings


def apply_enrollment(hit, data, selected_term, terms, course_ref_to_course):
    """Parse an already fetched enrollment package without network access."""
    course_code = int(hit["catalogNumber"])
    if len(hit["allCrossListedSubjects"]) > 1:
        enrollment_subjects = hit["allCrossListedSubjects"]
    else:
        enrollment_subjects = [hit["subject"]]

    subjects = {
        subject["shortDescription"].replace(" ", "") for subject in enrollment_subjects
    }
    course_ref = Course.Reference(subjects, course_code)

    if course_ref not in course_ref_to_course:
        logger.debug(f"Skipping unknown course: {course_ref}")
        return None

    course = course_ref_to_course[course_ref]
    enrollment_data = EnrollmentData.from_enrollment(hit, terms)

    course_instructors = {}
    course_meetings = set()
    section_count = len(data)

    logger.debug(f"Found {section_count} sections for {course_ref.get_identifier()}")

    for section in data:
        sections = section.get("sections", [])
        for s in sections:
            # Collect instructor names for this section
            section_instructor_names = []
            section_instructors = s.get("instructors", [])
            for instructor in section_instructors:
                name = instructor["name"]
                first = name["first"]
                last = name["last"]
                full_name = f"{first} {last}"
                email = instructor["email"]
                course_instructors.setdefault(full_name, email)
                section_instructor_names.append(full_name)

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

                exam_date = meeting.get("examDate")
                if not days and exam_date:  # Single event (exam)
                    # Convert exam date from epoch to date object
                    exam_date_obj = datetime.fromtimestamp(
                        exam_date / 1000, tz=CHICAGO_TZ
                    ).date()
                    # Use proper timezone handling for single meetings
                    single_meeting = convert_single_meeting(
                        meeting_date=exam_date_obj,
                        epoch_start_time_ms=start_time,
                        epoch_end_time_ms=end_time,
                    )
                    all_meeting_occurrences = [single_meeting] if single_meeting else []
                else:
                    # Recurring meetings
                    all_meeting_occurrences = generate_recurring_meetings(
                        start_date_epoch_ms=start_date,
                        end_date_epoch_ms=end_date,
                        epoch_start_time_ms=start_time,
                        epoch_end_time_ms=end_time,
                        days_of_week=days,
                    )

                location = None
                building = meeting.get("building")
                if building:
                    building_name = building["buildingName"]
                    coordinates = (building.get("latitude"), building.get("longitude"))
                    room = meeting.get("room", "No Assigned Room")

                    location = (
                        EnrollmentData.MeetingLocation.get_or_create_with_capacity(
                            building=building_name,
                            room=room,
                            coordinates=coordinates,
                            class_capacity=capacity,
                        )
                    )

                for index, (start, end) in enumerate(all_meeting_occurrences, start=1):
                    name = f"{section_identifier} #{index}"
                    course_meeting = EnrollmentData.Meeting(
                        start_time=start,
                        end_time=end,
                        type=meeting_type,
                        location=location,
                        name=name,
                        current_enrollment=current_enrollment,
                        instructors=section_instructor_names,
                        course_reference=course_ref,
                    )

                    course_meetings.add(course_meeting)

    enrollment_data.instructors = course_instructors
    logger.debug(
        f"Added {len(course_instructors)} instructors to {course_ref.get_identifier()}"
    )

    term_data = TermData(None, None)
    if course.term_data.get(selected_term):
        term_data = course.term_data[selected_term]

    term_data.enrollment_data = enrollment_data

    course.term_data[selected_term] = term_data

    # Set has_meetings field based on whether course has meeting data
    course.has_meetings = len(course_meetings) > 0

    return course_instructors, course_meetings, course_ref
