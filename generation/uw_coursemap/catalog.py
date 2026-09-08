"""Catalog grouping for website graph exports."""

from uw_coursemap.course import Course


def build_subject_to_courses(
    course_ref_to_course: dict[Course.Reference, Course],
) -> dict[str, set[Course]]:
    subject_to_courses = dict()
    for course in course_ref_to_course.values():
        subject = course.course_reference.subjects

        for s in subject:
            if s not in subject_to_courses:
                subject_to_courses[s] = set()
            subject_to_courses[s].add(course)

    return subject_to_courses
