import json
import re
from typing import Optional

from frozendict import frozendict

from json_serializable import JsonSerializable


def remove_extra_spaces(text: str):
    return re.sub(r"\s+", " ", text).strip()

def cleanup_course_reference_str(course_code: str):
    """Remove special HTML characters and clean up the course code."""
    if not course_code:
        return None
    course_code = remove_extra_spaces(course_code)
    return (
        course_code
        .replace("\u200b", " ")
        .replace("\u00a0", " ")
        .strip()
    )

class Identifiable:

        def get_identifier(self) -> str:
            raise NotImplementedError

class Course(JsonSerializable):

    class Reference(JsonSerializable, Identifiable):
        def __init__(self, subjects: set[str], course_number: int):
            self.subjects = subjects
            self.course_number = course_number

        @classmethod
        def from_json(cls, json_data) -> "Course.Reference":
            return Course.Reference(
                subjects=set(json_data["subjects"]),
                course_number=json_data["course_number"],
            )

        @classmethod
        def from_string(cls, course_reference_str: str):
            course_reference_str = cleanup_course_reference_str(course_reference_str)
            match = re.match(r"(\D+)(\d+)", course_reference_str)
            course_subject_str = match.group(1).replace(" ", "").strip()  # Only keep the subject
            raw_course_subjects = course_subject_str.split("/")
            course_subject = {str(subject).replace(" ", "") for subject in raw_course_subjects}
            course_number = int(match.group(2).strip())  # Convert to integer
            return Course.Reference(course_subject, course_number)

        def to_dict(self):
            return {
                "subjects": list(self.subjects),
                "course_number": self.course_number,
            }

        def get_identifier(self) -> str:
            subjects = "/".join(self.subjects)
            return f"{subjects} {self.course_number}"

        def __eq__(self, other):
            if not isinstance(other, Course.Reference):
                return False
            return self.subjects == other.subjects and self.course_number == other.course_number

        def __hash__(self):
            return hash(self.get_identifier())

        def __repr__(self):
            return f"CourseReference(subjects={self.subjects}, course_number={self.course_number})"

    class Prerequisites(JsonSerializable):

        def __init__(self, prerequisites_text, course_references):
            self.prerequisites_text = prerequisites_text
            self.course_references = course_references

        @classmethod
        def from_json(cls, json_data) -> "Course.Prerequisites":
            return Course.Prerequisites(
                prerequisites_text=json_data["prerequisites_text"],
                course_references=[
                    Course.Reference.from_json(course_ref) for course_ref in json_data["course_references"]
                ],
            )

        def to_dict(self):
            return {
                "prerequisites_text": self.prerequisites_text,
                "course_references": [course_ref.to_dict() for course_ref in self.course_references],
            }

        def __eq__(self, other):
            if not isinstance(other, Course.Prerequisites):
                return False
            return self.prerequisites_text == other.prerequisites_text and self.course_references == other.course_references

    def __init__(self, course_reference: Reference, course_title: str, description: str, prerequisites: Prerequisites):
        self.course_reference = course_reference
        self.course_title = course_title
        self.description = description
        self.prerequisites = prerequisites

    @classmethod
    def from_json(cls, json_data) -> "Course":
        return Course(
            course_reference=Course.Reference.from_json(json_data["course_reference"]),
            course_title=json_data["course_title"],
            description=json_data["description"],
            prerequisites=Course.Prerequisites.from_json(json_data["prerequisites"]),
        )

    def to_dict(self):
        return {
            "course_reference": self.course_reference.to_dict(),
            "course_title": self.course_title,
            "description": self.description,
            "prerequisites": self.prerequisites.to_dict()
        }

    @classmethod
    def from_block(cls, block):
        html_title = block.find("p", class_="courseblocktitle noindent")

        if not html_title:
            return None

        course_reference_str = html_title.find("span", class_="courseblockcode").get_text(strip=True)
        if not course_reference_str:
            return None
        course_reference = Course.Reference.from_string(course_reference_str)

        raw_title = html_title.get_text(strip=True)
        raw_course_title = raw_title.replace(course_reference_str, "").strip()
        course_title = raw_course_title.split("—", 1)[-1].strip() if "—" in raw_course_title else raw_course_title

        description = block.find("p", class_="courseblockdesc noindent").get_text(strip=True)

        cb_extras = block.find("div", class_="cb-extras")
        if not cb_extras:
            return Course(course_reference, course_title, description, )

        requisites_data = cb_extras.find("span", class_="cbextra-label", string=re.compile("Requisites:")).find_next(
            "span", class_="cbextra-data")
        requisites_text = requisites_data.get_text(strip=True)
        requisites_links = requisites_data.find_all("a")
        requisites_courses = set()
        for link in requisites_links:
            title = link.get("title", "").strip()
            requisites_courses.add(Course.Reference.from_string(title))

        requisites_courses.discard(course_reference)  # Remove self-reference

        course_prerequisite = Course.Prerequisites(requisites_text, requisites_courses)
        return Course(course_reference, course_title, description, course_prerequisite)

    def determine_parent(self):
        parent = None
        subjects = self.course_reference.subjects
        if len(subjects) > 1:
            parent = "CROSSLISTED"
        elif len(subjects) == 1:
            parent = next(iter(subjects))
        return parent

    def create_node(self):
        if self.determine_parent() != "CROSSLISTED":
            return frozendict({
                "data": frozendict({
                    "id": self.get_identifier(),
                    "parent": self.determine_parent(),
                    "description": self.description,
                }),
            })
        # Crosslisted courses are not children of a subject
        return frozendict({
            "data": frozendict({
                "id": self.get_identifier(),
                "description": self.description,
            }),
        })

    def create_edge(self, reference):
        return frozendict({
            "data": frozendict({
                "source": reference.get_identifier(),
                "target": self.get_identifier(),
            }),
        })

    def create_parent(self):
        return frozendict({
            "data": frozendict({
                "id": self.determine_parent(),
                "type": "compound",
            }),
        })

    def get_identifier(self):
        return self.course_reference.get_identifier()

    def get_subgraphs(self, courses, seen, graph_set_1, graph_set_2):
        if self.get_identifier() in seen:
            return
        seen.add(self.get_identifier())
        to_add = set()
        to_add.add(self.create_node())
        to_add.add(self.create_parent())
        for reference in self.prerequisites.course_references:
            if reference not in courses:
                print(f"Prerequisite not found in courses: {reference}")
                continue
            to_add.add(self.create_edge(reference))
            to_add.add(courses[reference].get_subgraphs(courses, seen, graph_set_1, graph_set_2))

        for graph_data in to_add:
            graph_set_1.add(graph_data)
            graph_set_2.add(graph_data)

    def get_short_summary(self):
        return f"""Course Title: {self.course_reference.get_identifier()} - {self.course_title}
        Course Description: {self.description}
        """

    def get_full_summary(self):
        req = self.prerequisites.prerequisites_text
        return f"""{self.get_short_summary()}
        Prerequisites: {req}
        """

    @classmethod
    def find_best_prerequisite(cls, course, prerequisites):
        """
        Finds the most relevant prerequisite for a given course using embeddings.

        Args:
            course: A Course object with attributes `description`.
            prerequisites: A list of Course objects, each with `description`.

        Returns:
            The most relevant prerequisite course.
        """
        # Get embedding for the main course
        course_embedding = get_embedding(course.get_full_summary())

        # Get embeddings for all prerequisites
        prerequisite_embeddings = [
            (prereq, get_embedding(prereq.get_short_summary())) for prereq in prerequisites
        ]

        # Compute similarity scores
        similarities = [
            (prereq, cosine_similarity(course_embedding, prereq_embedding))
            for prereq, prereq_embedding in prerequisite_embeddings
        ]

        # Find the prerequisite with the highest similarity score
        best_prerequisite = max(similarities, key=lambda x: x[1])

        # Return the course object of the best prerequisite
        return best_prerequisite[0]

    def optimize_prerequisites(self, course_ref_course, stats):
        if len(self.prerequisites.course_references) <= 1:
            return

        c = set()
        for reference in self.prerequisites.course_references:
            if reference not in course_ref_course:
                print(f"Prerequisite not found in courses: {reference}")
                continue
            course = course_ref_course[reference]
            c.add(course)

        best = self.find_best_prerequisite(self, c)
        print(f"Selected {best} as the best prerequisite for {self.get_identifier()} out of {len(c)} options")
        stats["removed_requisites"] += len(self.prerequisites.course_references) - 1
        self.prerequisites.course_references = {best.course_reference}

    def __eq__(self, other):
        return self.get_identifier() == other.get_identifier() and self.course_title == other.course_title and self.description == other.description

    def __hash__(self):
        return hash(self.get_identifier())

    def __repr__(self):
        return self.get_identifier()
