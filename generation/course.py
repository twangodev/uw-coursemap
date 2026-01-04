"""Course models - now using Pydantic schemas."""

from __future__ import annotations

import re
from logging import Logger
from typing import ClassVar

from bs4 import NavigableString
from pydantic import ConfigDict

from schemas.course import (
    CourseReference as _CourseReferenceBase,
    CoursePrerequisites,
    Course as _CourseBase,
)
from schemas.enrollment import TermData
from schemas.grades import GradeData
from requirement_ast import (
    tokenize_requisites,
    RequirementParser,
)

__all__ = [
    "Course",
    "CourseReference",
    "CoursePrerequisites",
    "TermData",
    "GradeData",
]


def remove_extra_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def cleanup_course_reference_str(course_code: str) -> str | None:
    """Remove special HTML characters and clean up the course code."""
    if not course_code:
        return None
    course_code = remove_extra_spaces(course_code)
    return course_code.replace("\u200b", " ").replace("\u00a0", " ").strip()


class CourseReference(_CourseReferenceBase):
    """Extended CourseReference for backward compatibility."""

    # Allow use as dict key
    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_string(cls, course_reference_str: str) -> CourseReference:
        """Parse a course reference from a string like 'CS/ECE 252'."""
        course_reference_str = cleanup_course_reference_str(course_reference_str)
        if not course_reference_str:
            raise ValueError("Empty course reference string")

        match = re.match(r"(\D+)(\d+)", course_reference_str)
        if not match:
            raise ValueError(f"Invalid course reference format: {course_reference_str}")

        course_subject_str = match.group(1).replace(" ", "").strip()
        raw_course_subjects = course_subject_str.split("/")
        course_subjects = frozenset(
            subject.replace(" ", "") for subject in raw_course_subjects
        )
        course_number = int(match.group(2).strip())

        return cls(subjects=course_subjects, course_number=course_number)

    @classmethod
    def from_json(cls, json_data: dict) -> CourseReference:
        """Create CourseReference from JSON dict."""
        return cls(
            subjects=frozenset(json_data["subjects"]),
            course_number=json_data["course_number"],
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


# Backward compatibility alias
Course_Reference = CourseReference


class Course(_CourseBase):
    """Extended Course with HTML parsing and factory methods."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    # Nested class for backward compatibility (ClassVar so Pydantic ignores them)
    Reference: ClassVar[type] = CourseReference
    Prerequisites: ClassVar[type] = CoursePrerequisites

    @classmethod
    def from_json(cls, json_data: dict) -> Course:
        """Create Course from JSON dict."""
        from enrollment_data import GradeData, TermData, EnrollmentData

        optimized_prerequisites = None
        if json_data.get("optimized_prerequisites"):
            optimized_prerequisites = [
                CourseReference.from_json(ref)
                for ref in json_data["optimized_prerequisites"]
            ]

        cumulative_grade_data = None
        if json_data.get("cumulative_grade_data"):
            cumulative_grade_data = GradeData.from_json(
                json_data["cumulative_grade_data"]
            )

        # Parse prerequisites
        prereqs_data = json_data.get("prerequisites", {})
        prerequisites = CoursePrerequisites(
            prerequisites_text=prereqs_data.get("prerequisites_text", ""),
            linked_requisite_text=prereqs_data.get("linked_requisite_text", []),
            course_references=[
                CourseReference.from_json(ref)
                for ref in prereqs_data.get("course_references", [])
            ],
            abstract_syntax_tree=prereqs_data.get("abstract_syntax_tree"),
        )

        # Parse term data
        term_data = {}
        for term, data in json_data.get("term_data", {}).items():
            enrollment = None
            if data.get("enrollment_data"):
                enrollment = EnrollmentData.from_json(data["enrollment_data"])
            grade = None
            if data.get("grade_data"):
                grade = GradeData.from_json(data["grade_data"])
            term_data[term] = TermData(enrollment_data=enrollment, grade_data=grade)

        return cls(
            course_reference=CourseReference.from_json(json_data["course_reference"]),
            course_title=json_data["course_title"],
            description=json_data["description"],
            prerequisites=prerequisites,
            optimized_prerequisites=optimized_prerequisites,
            cumulative_grade_data=cumulative_grade_data,
            term_data=term_data,
            similar_courses=[
                CourseReference.from_json(ref)
                for ref in json_data.get("similar_courses", [])
            ],
            keywords=json_data.get("keywords", []),
            satisfies=[
                CourseReference.from_json(ref) for ref in json_data.get("satisfies", [])
            ],
            has_meetings=json_data.get("has_meetings", False),
        )

    @classmethod
    def from_block(cls, block, logger: Logger) -> Course | None:
        """Parse a course from HTML block."""
        html_title = block.find("p", class_="courseblocktitle noindent")

        if not html_title:
            return None

        course_reference_str = html_title.find(
            "span", class_="courseblockcode"
        ).get_text(strip=True)
        if not course_reference_str:
            return None
        course_reference = CourseReference.from_string(course_reference_str)

        raw_title = html_title.get_text(strip=True)
        raw_course_title = raw_title.replace(course_reference_str, "").strip()
        course_title = (
            raw_course_title.split("—", 1)[-1].strip()
            if "—" in raw_course_title
            else raw_course_title
        )

        description = block.find("p", class_="courseblockdesc noindent").get_text(
            strip=True
        )

        cb_extras = block.find("div", class_="cb-extras")
        basic_prerequisites = CoursePrerequisites(
            prerequisites_text="",
            linked_requisite_text=[],
            course_references=[],
            abstract_syntax_tree=None,
        )
        basic_course = cls(
            course_reference=course_reference,
            course_title=course_title,
            description=description,
            prerequisites=basic_prerequisites,
            optimized_prerequisites=None,
            cumulative_grade_data=None,
            term_data={},
        )
        if not cb_extras:
            return basic_course

        requisites_header = cb_extras.find(
            "span", class_="cbextra-label", string=re.compile("Requisites:")
        )
        if not requisites_header:
            return basic_course

        requisites_data = requisites_header.find_next("span", class_="cbextra-data")
        requisites_text = requisites_data.get_text(strip=True)

        requisites_courses = set()
        linked_requisite_text = []

        for node in requisites_data.contents:
            if isinstance(node, NavigableString):
                linked_requisite_text.append(node.get_text())
            elif node.name == "a":
                title = node.get("title", "").strip()
                reference = CourseReference.from_string(title)

                requisites_courses.add(reference)
                linked_requisite_text.append(reference)
            else:
                linked_requisite_text.append(node.get_text(strip=True))

        tokens = tokenize_requisites(linked_requisite_text)

        parser = RequirementParser(tokens)
        tree = None
        try:
            tree = parser.parse()
        except SyntaxError as se:
            logger.warning(
                f"Syntax error in course {course_reference}: {se}. See text: {requisites_text}"
            )

        requisites_courses.discard(course_reference)  # Remove self-reference

        course_prerequisite = CoursePrerequisites(
            prerequisites_text=requisites_text,
            linked_requisite_text=linked_requisite_text,
            course_references=list(requisites_courses),
            abstract_syntax_tree=tree,
        )
        return cls(
            course_reference=course_reference,
            course_title=course_title,
            description=description,
            prerequisites=course_prerequisite,
            optimized_prerequisites=None,
            cumulative_grade_data=None,
            term_data={},
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


# Rebuild model to ensure validators are properly inherited
Course.model_rebuild()
