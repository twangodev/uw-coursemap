"""One source adapter per spider; all outbound ingestion goes through Scrapy."""

import json
import os
import re
from urllib.parse import urlparse

import scrapy
from scrapy.http import JsonRequest

from .models import CourseReference, digest
from .derive import plain


def item(kind, key, payload, response):
    return {
        "kind": kind,
        "key": str(key),
        "payload": payload,
        "source_url": response.url,
    }


class SourceSpider(scrapy.Spider):
    def __init__(self, store, run, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self.run_id = run
        self.semester = store.run(run)["semester"]
        self.failures = 0

    def failed(self, failure):
        self.failures += 1
        self.logger.error("Request failed: %s", failure.request.url)

    def request(self, url, callback, **kwargs):
        return scrapy.Request(url, callback=callback, errback=self.failed, **kwargs)


class CatalogSpider(SourceSpider):
    name = "catalog"
    allowed_domains = ["guide.wisc.edu"]

    async def start(self):
        yield self.request("https://guide.wisc.edu/sitemap.xml", self.sitemap)

    def sitemap(self, response):
        from scrapy.selector import Selector

        selector = Selector(text=response.body.decode(), type="xml")
        selector.remove_namespaces()
        urls = sorted(set(selector.css("loc::text").getall()))
        departments = [url for url in urls if re.search(r"/courses/.+", url)]
        if not departments:
            raise ValueError("Catalog sitemap contains no departments")
        for url in departments:
            yield self.request(url, self.department)

    def department(self, response):
        from bs4 import BeautifulSoup
        from course import Course

        soup = BeautifulSoup(response.body, "html.parser")
        title = soup.find(class_="page-title")
        match = re.fullmatch(
            r"(.*)\((.*)\)", title.get_text(strip=True) if title else ""
        )
        if not match:
            raise ValueError("Missing department heading")
        abbreviation = match[2].replace(" ", "")
        yield item("subjects", abbreviation, {"name": match[1].strip()}, response)
        blocks = soup.select("div.courseblock")
        if not blocks:
            raise ValueError("Department contains no course blocks")
        for block in blocks:
            course = Course.from_block(block, self.logger)
            if course is None:
                raise ValueError("Could not parse course block")
            payload = plain(course)
            payload["course_reference"]["subjects"].sort()
            yield item(
                "courses", course.course_reference.get_identifier(), payload, response
            )


class MadgradesSpider(SourceSpider):
    name = "madgrades"
    allowed_domains = ["api.madgrades.com"]
    base = "https://api.madgrades.com/v1/"

    def request(self, url, callback, **kwargs):
        if (
            urlparse(url).hostname != "api.madgrades.com"
            or urlparse(url).scheme != "https"
        ):
            raise ValueError("Unexpected Madgrades URL")
        key = os.environ.get("MADGRADES_API_KEY")
        if not key:
            raise ValueError("MADGRADES_API_KEY is required")
        return super().request(
            url, callback, headers={"Authorization": f"Token token={key}"}, **kwargs
        )

    async def start(self):
        yield self.request(self.base + "terms", self.terms)
        yield self.request(self.base + "courses?per_page=100&page=1", self.courses)

    def terms(self, response):
        data = json.loads(response.body)
        if not data:
            raise ValueError("Empty Madgrades terms")
        for code, name in data.items():
            yield item("terms", code, {"name": name}, response)

    def courses(self, response):
        data = json.loads(response.body)
        page, total = int(data["currentPage"]), int(data["totalPages"])
        if not 1 <= page <= total or not data["results"]:
            raise ValueError("Invalid Madgrades pagination")
        if page == 1:
            for number in range(2, total + 1):
                yield self.request(
                    f"{self.base}courses?per_page=100&page={number}", self.courses
                )
        for course in data["results"]:
            reference = CourseReference(
                subjects=sorted(
                    {s["abbreviation"].replace(" ", "") for s in course["subjects"]}
                ),
                course_number=int(course["number"]),
            )
            yield self.request(
                course["url"] + "/grades",
                self.grades,
                cb_kwargs={
                    "reference": reference.model_dump(),
                    "source_id": str(course.get("uuid", course["url"])),
                },
            )

    def grades(self, response, reference, source_id):
        payload = json.loads(response.body)
        payload.update(course_reference=reference, source_id=source_id)
        yield item("grades", source_id, payload, response)


class EnrollmentSpider(SourceSpider):
    name = "enrollment"
    allowed_domains = ["public.enroll.wisc.edu"]
    base = "https://public.enroll.wisc.edu/api/search/v1"

    async def start(self):
        yield self.request(self.base + "/aggregate", self.terms)

    def terms(self, response):
        terms = json.loads(response.body)["terms"]
        selected = None
        for term in terms:
            code = str(term["termCode"])
            yield item(
                "terms",
                code,
                {
                    "name": term["shortDescription"],
                    "start": term["instructionBeginDate"],
                    "end": term["instructionEndDate"],
                },
                response,
            )
            if code == self.semester:
                selected = term
        if selected is None:
            raise ValueError(
                f"Semester {self.semester} is not available from enrollment API"
            )
        yield self.page(1)

    def page(self, page):
        return JsonRequest(
            self.base,
            data={
                "selectedTerm": self.semester,
                "queryString": "",
                "filters": [],
                "page": page,
                "pageSize": 100,
            },
            callback=self.hits,
            cb_kwargs={"page": page},
            errback=self.failed,
        )

    def hits(self, response, page):
        data = json.loads(response.body)
        found = int(data["found"])
        expected = min(100, found - (page - 1) * 100)
        if found <= 0 or len(data["hits"]) != expected:
            raise ValueError("Incomplete enrollment search page")
        if page == 1:
            for number in range(2, (found + 99) // 100 + 1):
                yield self.page(number)
        for hit in data["hits"]:
            subjects = (
                hit["allCrossListedSubjects"]
                if len(hit["allCrossListedSubjects"]) > 1
                else [hit["subject"]]
            )
            reference = CourseReference(
                subjects=sorted(
                    {s["shortDescription"].replace(" ", "") for s in subjects}
                ),
                course_number=int(hit["catalogNumber"]),
            )
            url = f"{self.base}/enrollmentPackages/{self.semester}/{hit['subject']['subjectCode']}/{hit['courseId']}"
            yield self.request(
                url,
                self.package,
                cb_kwargs={"hit": hit, "reference": reference.model_dump()},
            )

    def package(self, response, hit, reference):
        sections = json.loads(response.body)
        if not isinstance(sections, list):
            raise ValueError("Invalid enrollment package")
        key = f"{self.semester}:{hit['subject']['subjectCode']}:{hit['courseId']}"
        yield item(
            "offerings",
            key,
            {
                "term": self.semester,
                "course_reference": reference,
                "hit": hit,
                "sections": sections,
            },
            response,
        )
        for package in sections:
            for section in package["sections"]:
                for instructor in section.get("instructors", []):
                    name = f"{instructor['name']['first']} {instructor['name']['last']}"
                    yield item(
                        "instructors",
                        digest(name),
                        {"name": name, "email": instructor.get("email")},
                        response,
                    )


class InstructorSpider(SourceSpider):
    name = "instructors"
    allowed_domains = ["guide.wisc.edu", "www.ratemyprofessors.com"]

    async def start(self):
        yield self.request("https://guide.wisc.edu/faculty/", self.faculty)
        yield self.request("https://www.ratemyprofessors.com/", self.authentication)

    def faculty(self, response):
        from instructors import parse_faculty

        faculty = parse_faculty(response.body)
        if not faculty:
            raise ValueError("Faculty page contains no records")
        for name, (position, department, credentials) in faculty.items():
            yield item(
                "faculty",
                name,
                {
                    "name": name,
                    "position": position,
                    "department": department,
                    "credentials": credentials,
                },
                response,
            )

    def authentication(self, response):
        from instructors import graph_ql_query, produce_query

        match = re.search(
            r'"REACT_APP_GRAPHQL_AUTH"\s*:\s*"([^"]+)"', response.body.decode()
        )
        if not match:
            raise ValueError("RMP authentication configuration missing")
        names = {
            row["name"]
            for row in self.store.records(self.run_id, "instructors").values()
        }
        for grades in self.store.records(self.run_id, "grades").values():
            for offering in grades["courseOfferings"]:
                for section in offering["sections"]:
                    names.update(i["name"] for i in section["instructors"] if i["name"])
        for name in sorted(names):
            yield JsonRequest(
                "https://www.ratemyprofessors.com/graphql",
                data={"query": graph_ql_query, "variables": produce_query(name)},
                headers={"Authorization": f"Basic {match[1]}"},
                callback=self.rating,
                cb_kwargs={"name": name},
                errback=self.failed,
            )

    def rating(self, response, name):
        data = json.loads(response.body)
        if data.get("errors"):
            raise ValueError("RMP returned GraphQL errors")
        candidates = [
            edge["node"] for edge in data["data"]["newSearch"]["teachers"]["edges"]
        ]
        yield item("ratings", name, {"name": name, "candidates": candidates}, response)


SPIDERS = {
    spider.name: spider
    for spider in (CatalogSpider, MadgradesSpider, EnrollmentSpider, InstructorSpider)
}
