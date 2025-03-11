import asyncio
import re
from json import JSONDecodeError

from enrollment_data import EnrollmentData
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
            subjects = "/".join(sorted(self.subjects))
            return f"{subjects} {self.course_number}"

        def __eq__(self, other):
            if not isinstance(other, Course.Reference):
                return False
            return self.subjects == other.subjects and self.course_number == other.course_number

        def __hash__(self):
            return hash(self.get_identifier())

        def __repr__(self):
            return f"CourseReference(subjects={self.subjects}, course_number={self.course_number})"

        def __str__(self):
            return self.get_identifier()

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

    def __init__(
            self,
            course_reference: Reference,
            course_title: str,
            description: str,
            prerequisites: Prerequisites,
            optimized_prerequisites: Prerequisites | None,
            madgrades_data,
            enrollment_data: dict[str, EnrollmentData],
    ):
        self.course_reference = course_reference
        self.course_title = course_title
        self.description = description
        self.prerequisites = prerequisites
        self.optimized_prerequisites = optimized_prerequisites
        self.madgrades_data = madgrades_data
        self.enrollment_data = enrollment_data

    @classmethod
    def from_json(cls, json_data) -> "Course":
        optimized_prerequisites = None
        if json_data["optimized_prerequisites"]:
            optimized_prerequisites = Course.Prerequisites.from_json(json_data["optimized_prerequisites"])

        madgrades_data = None
        if json_data["madgrades_data"]:
            madgrades_data = MadgradesData.from_json(json_data["madgrades_data"])

        return Course(
            course_reference=Course.Reference.from_json(json_data["course_reference"]),
            course_title=json_data["course_title"],
            description=json_data["description"],
            prerequisites=Course.Prerequisites.from_json(json_data["prerequisites"]),
            optimized_prerequisites=optimized_prerequisites,
            madgrades_data=madgrades_data,
            enrollment_data={term: EnrollmentData.from_json(data) for term, data in json_data["enrollment_data"].items()}
        )

    def to_dict(self):
        return {
            "course_reference": self.course_reference.to_dict(),
            "course_title": self.course_title,
            "description": self.description,
            "prerequisites": self.prerequisites.to_dict(),
            "optimized_prerequisites": self.optimized_prerequisites.to_dict() if self.optimized_prerequisites else None,
            "madgrades_data": self.madgrades_data.to_dict() if self.madgrades_data else None,
            "enrollment_data": {term: data.to_dict() for term, data in self.enrollment_data.items()}
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
        basic_course = Course(course_reference, course_title, description, Course.Prerequisites("", set()), None, None,
                              {})
        if not cb_extras:
            return basic_course

        requisites_header = cb_extras.find("span", class_="cbextra-label", string=re.compile("Requisites:"))
        if not requisites_header:
            return basic_course

        requisites_data = requisites_header.find_next("span", class_="cbextra-data")
        requisites_text = requisites_data.get_text(strip=True)
        requisites_links = requisites_data.find_all("a")
        requisites_courses = set()
        for link in requisites_links:
            title = link.get("title", "").strip()
            requisites_courses.add(Course.Reference.from_string(title))

        requisites_courses.discard(course_reference)  # Remove self-reference

        course_prerequisite = Course.Prerequisites(requisites_text, requisites_courses)
        return Course(course_reference, course_title, description, course_prerequisite, None, None, {})

    def determine_parent(self):
        parent = None
        subjects = self.course_reference.subjects
        if len(subjects) > 1:
            parent = "CROSSLISTED"
        elif len(subjects) == 1:
            parent = next(iter(subjects))
        return parent

    def get_identifier(self):
        return self.course_reference.get_identifier()

    def get_short_summary(self):
        return f"""Course Title: {self.course_reference.get_identifier()} - {self.course_title}
        Course Description: {self.description}
        """

    def get_full_summary(self):
        req = self.prerequisites.prerequisites_text
        return f"""{self.get_short_summary()}
        Prerequisites: {req}
        """

    def __eq__(self, other):
        return self.get_identifier() == other.get_identifier() and self.course_title == other.course_title and self.description == other.description

    def __hash__(self):
        return hash(self.get_identifier())

    def __repr__(self):
        return self.get_identifier()


class GradeData(JsonSerializable):

    def __init__(self, total, a, ab, b, bc, c, d, f, satisfactory, unsatisfactory, credit, no_credit, passed,
                 incomplete, no_work, not_reported, other):
        self.total = total
        self.a = a
        self.ab = ab
        self.b = b
        self.bc = bc
        self.c = c
        self.d = d
        self.f = f
        self.satisfactory = satisfactory
        self.unsatisfactory = unsatisfactory
        self.credit = credit
        self.no_credit = no_credit
        self.passed = passed
        self.incomplete = incomplete
        self.no_work = no_work
        self.not_reported = not_reported
        self.other = other

    @classmethod
    def from_madgrades(cls, json_data) -> "GradeData":
        return GradeData(
            total=json_data["total"],
            a=json_data["aCount"],
            ab=json_data["abCount"],
            b=json_data["bCount"],
            bc=json_data["bcCount"],
            c=json_data["cCount"],
            d=json_data["dCount"],
            f=json_data["fCount"],
            satisfactory=json_data["sCount"],
            unsatisfactory=json_data["uCount"],
            credit=json_data["crCount"],
            no_credit=json_data["nCount"],
            passed=json_data["pCount"],
            incomplete=json_data["iCount"],
            no_work=json_data["nwCount"],
            not_reported=json_data["nrCount"],
            other=json_data["otherCount"]
        )

    @classmethod
    def from_json(cls, json_data) -> "JsonSerializable":
        return GradeData(
            total=json_data["total"],
            a=json_data["a"],
            ab=json_data["ab"],
            b=json_data["b"],
            bc=json_data["bc"],
            c=json_data["c"],
            d=json_data["d"],
            f=json_data["f"],
            satisfactory=json_data["satisfactory"],
            unsatisfactory=json_data["unsatisfactory"],
            credit=json_data["credit"],
            no_credit=json_data["no_credit"],
            passed=json_data["passed"],
            incomplete=json_data["incomplete"],
            no_work=json_data["no_work"],
            not_reported=json_data["not_reported"],
            other=json_data["other"]
        )

    def to_dict(self):
        return {
            "total": self.total,
            "a": self.a,
            "ab": self.ab,
            "b": self.b,
            "bc": self.bc,
            "c": self.c,
            "d": self.d,
            "f": self.f,
            "satisfactory": self.satisfactory,
            "unsatisfactory": self.unsatisfactory,
            "credit": self.credit,
            "no_credit": self.no_credit,
            "passed": self.passed,
            "incomplete": self.incomplete,
            "no_work": self.no_work,
            "not_reported": self.not_reported,
            "other": self.other
        }


class MadgradesData(JsonSerializable):

    def __init__(self, cumulative, by_term):
        self.cumulative = cumulative
        self.by_term = by_term

    @classmethod
    def from_json(cls, json_data) -> "MadgradesData":
        return MadgradesData(
            cumulative=GradeData.from_json(json_data["cumulative"]),
            by_term={term: GradeData.from_json(data) for term, data in json_data["by_term"].items()}
        )

    def to_dict(self):
        return {
            "cumulative": self.cumulative.to_dict(),
            "by_term": {term: data.to_dict() for term, data in self.by_term.items()}
        }

    @classmethod
    async def from_madgrades_async(cls, session, url, madgrades_api_key, logger, attempts=3) -> "MadgradesData":
        auth_header = {"Authorization": f"Token token={madgrades_api_key}"}

        try:
            async with session.get(url, headers=auth_header) as response:
                data = await response.json()
        except (JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to fetch madgrades data from {url}: {str(e)}")
            if attempts > 0:
                logger.info(f"Retrying {attempts} more times...")
                await asyncio.sleep(1)
                return await MadgradesData.from_madgrades_async(session, url, madgrades_api_key, logger, attempts - 1)

        cumulative = GradeData.from_madgrades(data["cumulative"])
        course_offerings = data["courseOfferings"]

        by_term = {}
        for offering in course_offerings:
            term_code = offering["termCode"]
            grade_data = GradeData.from_madgrades(offering["cumulative"])
            by_term[term_code] = grade_data

        return MadgradesData(cumulative=cumulative, by_term=by_term)
