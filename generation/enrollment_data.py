import asyncio
from json import JSONDecodeError

from json_serializable import JsonSerializable
from safe_parse import safe_int


class EnrollmentData(JsonSerializable):
    class School(JsonSerializable):

        def __init__(self, name, abbreviation, url):
            self.name = name
            self.abbreviation = abbreviation
            self.url = url

        @classmethod
        def from_json(cls, data) -> 'EnrollmentData.School':
            return EnrollmentData.School(
                name=data["name"],
                abbreviation=data["abbreviation"],
                url=data["url"]
            )

        def to_dict(self) -> dict:
            return {
                "name": self.name,
                "abbreviation": self.abbreviation,
                "url": self.url
            }

        @classmethod
        def from_enrollment(cls, data) -> 'EnrollmentData.School':
            return EnrollmentData.School(
                name=data["shortDescription"],
                abbreviation=data["academicOrgCode"],
                url=data["schoolCollegeURI"]
            )

        def __str__(self):
            return self.name

        def __eq__(self, other):
            return self.name == other.name and self.abbreviation == other.abbreviation and self.url == other.url

    def __init__(
            self,
            school: School | None,
            last_taught_term: str,
            typically_offered: str,
            credit_count: tuple[int, int],
            general_education: bool,
            ethnics_studies: bool,
            instructors,
    ):
        self.school = school
        self.last_taught_term = last_taught_term
        self.typically_offered = typically_offered
        self.credit_count = credit_count
        self.general_education = general_education
        self.ethnics_studies = ethnics_studies
        self.instructors = instructors

    @classmethod
    def from_json(cls, data) -> 'EnrollmentData':
        return EnrollmentData(
            school=EnrollmentData.School.from_json(data["school"]),
            last_taught_term=data["last_taught_term"],
            typically_offered=data["typically_offered"],
            credit_count=(data["credit_count"][0], data["credit_count"][1]),
            general_education=data["general_education"],
            ethnics_studies=data["ethnics_studies"],
            instructors=data["instructors"]
        )

    @classmethod
    def from_enrollment(cls, data, terms) -> 'EnrollmentData':
        last_taught_term_code = safe_int(data["lastTaught"])
        last_taught_term = None
        if last_taught_term_code and last_taught_term_code in terms:
            last_taught_term = terms[last_taught_term_code]
        return EnrollmentData(
            school=EnrollmentData.School.from_enrollment(data["subject"]["schoolCollege"]),
            last_taught_term=last_taught_term,
            typically_offered=data["typicallyOffered"],
            credit_count=(data["minimumCredits"], data["maximumCredits"]),
            general_education=data["generalEd"] is not None,
            ethnics_studies=data["ethnicStudies"] is not None,
            instructors={}
        )

    def to_dict(self) -> dict:
        return {
            "school": self.school.to_dict(),
            "last_taught_term": self.last_taught_term,
            "typically_offered": self.typically_offered,
            "credit_count": [self.credit_count[0], self.credit_count[1]],
            "general_education": self.general_education,
            "ethnics_studies": self.ethnics_studies,
            "instructors": self.instructors
        }

class GradeData(JsonSerializable):

    def __init__(
            self,
            total,
            a,
            ab,
            b,
            bc,
            c,
            d,
            f,
            satisfactory,
            unsatisfactory,
            credit,
            no_credit,
            passed,
            incomplete,
            no_work,
            not_reported,
            other,
            instructors: set[str] | None,
    ):
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
        self.instructors = instructors

    @classmethod
    def empty(cls):
        return GradeData(
            total=0,
            a=0,
            ab=0,
            b=0,
            bc=0,
            c=0,
            d=0,
            f=0,
            satisfactory=0,
            unsatisfactory=0,
            credit=0,
            no_credit=0,
            passed=0,
            incomplete=0,
            no_work=0,
            not_reported=0,
            other=0,
            instructors=set()
        )

    def merge_with(self, other: "GradeData") -> "GradeData":
        return GradeData(
            total=self.total + other.total,
            a=self.a + other.a,
            ab=self.ab + other.ab,
            b=self.b + other.b,
            bc=self.bc + other.bc,
            c=self.c + other.c,
            d=self.d + other.d,
            f=self.f + other.f,
            satisfactory=self.satisfactory + other.satisfactory,
            unsatisfactory=self.unsatisfactory + other.unsatisfactory,
            credit=self.credit + other.credit,
            no_credit=self.no_credit + other.no_credit,
            passed=self.passed + other.passed,
            incomplete=self.incomplete + other.incomplete,
            no_work=self.no_work + other.no_work,
            not_reported=self.not_reported + other.not_reported,
            other=self.other + other.other,
            instructors=self.instructors.union(other.instructors) if self.instructors and other.instructors else self.instructors or other.instructors
        )

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
            other=json_data["otherCount"],
            instructors=None
        )

    @classmethod
    def from_json(cls, json_data) -> "GradeData":
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
            other=json_data["other"],
            instructors=set(json_data["instructors"]) if json_data["instructors"] else None
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
            "other": self.other,
            "instructors": list(self.instructors) if self.instructors else None
        }


class MadgradesData:

    def __init__(self, cumulative, by_term: dict[str, GradeData]):
        self.cumulative = cumulative
        self.by_term = by_term

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
            term_code = str(offering["termCode"])
            grade_data = GradeData.from_madgrades(offering["cumulative"])

            instructors = set()
            sections = offering["sections"]

            for section in sections:
                for instructor in section["instructors"]:
                    instructors.add(instructor["name"])

            grade_data.instructors = set(instructors)

            by_term[term_code] = grade_data

        return MadgradesData(cumulative=cumulative, by_term=by_term)


class TermData(JsonSerializable):

    def __init__(
            self,
            enrollment_data: EnrollmentData | None,
            grade_data: GradeData | None,
    ):
        self.enrollment_data = enrollment_data
        self.grade_data = grade_data


    @classmethod
    def from_json(cls, data) -> 'TermData':
        enrollment_data = None
        if data["enrollment_data"]:
            enrollment_data = EnrollmentData.from_json(data["enrollment_data"])
        grade_data = None
        if data["grade_data"]:
            grade_data = GradeData.from_json(data["grade_data"])
        return TermData(
            enrollment_data=enrollment_data,
            grade_data=grade_data,
        )

    def to_dict(self) -> dict:
        return {
            "enrollment_data": self.enrollment_data.to_dict() if self.enrollment_data else None,
            "grade_data": self.grade_data.to_dict() if self.grade_data else None,
        }


