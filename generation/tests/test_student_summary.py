import copy
import unittest
from uw_coursemap.student_context import grade_sentence, match_name
from uw_coursemap.student_summary import generate_student, validate_claims


def grade(term, a, b, section=1):
    return {
        "term_id": term,
        "term_name": term,
        "counts": {"a": a, "ab": 0, "b": b, "bc": 0, "c": 0, "d": 0, "f": 0},
        "citation": {
            "type": "grade",
            "run_id": "run",
            "table": "section_grades_latest",
            "term_id": term,
            "section_number": section,
        },
    }


def review(id, instructor):
    return {
        "id": id,
        "instructor_id": instructor,
        "instructor_name": instructor,
        "course_id": "COMPSCI 300",
        "source_review_id": id,
        "source_url": "https://example.com/" + id,
        "date": "2025-01-01",
        "comment": "Clear lectures and useful projects.",
    }


class StudentSummaryTests(unittest.TestCase):
    def test_grades_deduplicate_weight_and_use_last_three_usable_terms(self):
        data = [
            grade("1", 10, 0),
            grade("2", 10, 10),
            grade("3", 0, 10),
            grade("4", 10, 0),
            grade("4", 0, 30, 2),
            grade("5", 0, 0),
        ]
        data.append(copy.deepcopy(data[3]))
        result = grade_sentence(data)
        self.assertNotIn("1:", result["text"])
        self.assertIn("4: 3.25 GPA, 25.0% A/AB (n=40 letter grades)", result["text"])
        self.assertEqual(len(result["citations"]), 4)
        self.assertEqual(set(result), {"text", "citations"})
        data[-1]["counts"]["a"] = None
        self.assertIsNone(grade_sentence([data[-1]]))

    def test_joint_teaching_and_ambiguous_names(self):
        row = grade("1", 10, 10)
        row["joint"] = True
        self.assertIn("jointly taught", grade_sentence([row])["text"])
        self.assertIsNone(match_name("J Smith", ("Jane Smith", "John Smith")))
        self.assertEqual(
            match_name("Jane Smith", ("Jane Smith", "John Smith")), "Jane Smith"
        )

    def test_claims_reject_other_scope_citations_and_generated_grades(self):
        request = {
            "mode": "professor",
            "instructor_name": "Jane Doe",
            "reviews": [{"citation_id": "review:1"}],
        }
        output = {
            "summary": [
                {"text": "Jane Doe explains clearly.", "review_ids": ["review:1"]}
            ],
            "quick_take": [],
            "difficulty_workload": [],
            "student_experience": [],
        }
        validate_claims(output, request)
        for text, ids in [
            ("Someone explains clearly.", ["review:1"]),
            ("Jane Doe gives a 4.0 GPA.", ["review:1"]),
            ("Jane Doe explains clearly.", ["review:2"]),
        ]:
            output["summary"][0].update(text=text, review_ids=ids)
            with self.assertRaises(ValueError):
                validate_claims(output, request)

    def test_independent_professors_history_and_missing_reviews(self):
        calls = []

        def fake(profile, task, request):
            calls.append(request)
            result = {
                k: []
                for k in (
                    "summary",
                    "quick_take",
                    "difficulty_workload",
                    "student_experience",
                )
            }
            name = request["instructor_name"] or "Historical reviewers"
            result["quick_take" if request["mode"] == "overview" else "summary"] = [
                {"text": name + " reported clear lectures.", "review_ids": ["review:1"]}
            ]
            return result, {"total_tokens": 5}

        people = [
            {
                "name": "Jane Doe",
                "instructor_uid": "uw:1",
                "rmp_instructor_id": "rmp:1",
                "reviews": [review("1", "rmp:1")],
                "grade_records": [grade("1", 1, 1)],
            },
            {
                "name": "New Teacher",
                "instructor_uid": "uw:2",
                "rmp_instructor_id": None,
                "reviews": [],
                "grade_records": [],
            },
        ]
        base = {
            "search_profile": {
                "status": "valid",
                "value": {"summary": "Original catalog summary"},
            },
            "requirements": {"status": "needs_review", "value": {"nodes": []}},
            "student_experience": {"status": "valid", "value": {}},
        }
        payload = {
            "source_run": "run",
            "summary_seed": {"job_id": "parent", "output": {"sections": base}},
            "student_context": {
                "course_id": "COMPSCI 300",
                "term_id": "1272",
                "term_name": "Fall 2026",
                "offered": True,
                "current_instructors": people,
                "historical_reviews": [review("2", "rmp:old")],
                "grade_records": [grade("1", 1, 1)],
            },
        }
        result, _ = generate_student(
            {"model": "test", "revision": "abc", "max_output_tokens": 1000},
            {"version": 1},
            payload,
            generate=fake,
        )
        self.assertEqual({k: result["sections"][k] for k in base}, base)
        section = result["sections"]["student_summary"]
        self.assertEqual(section["status"], "valid")
        current = section["value"]["current_instructors"]
        self.assertEqual(current[1]["review_status"], "no_course_reviews")
        self.assertEqual(
            current[0]["summary"][0]["citations"][0]["source_instructor_id"], "rmp:1"
        )
        self.assertEqual(
            section["value"]["historical_context"][0]["citations"][0][
                "source_instructor_id"
            ],
            "rmp:old",
        )
        self.assertEqual([r["instructor_id"] for r in calls[-1]["reviews"]], ["rmp:1"])

        payload["summary_seed"] = {"job_id": "previous", "output": result}
        before = len(calls)
        resumed, _ = generate_student(
            {"model": "test", "revision": "abc", "max_output_tokens": 1000},
            {"version": 1},
            payload,
            generate=fake,
        )
        self.assertEqual(len(calls), before)
        self.assertEqual(
            resumed["sections"]["student_summary"]["value"], section["value"]
        )
        self.assertEqual(len(resumed["provenance"]["reused_scopes"]), 3)

    def test_current_roster_uses_term_and_deduplicates_cross_listings(self):
        from uw_coursemap.student_context import StudentContext

        class DB:
            def execute(self, *args):
                return []

        person = {"name": {"first": "Jane", "last": "Doe"}, "netid": "jdoe"}
        current = {
            "course_reference": {"subjects": ["COMPSCI"], "course_number": 300},
            "term": "1272",
            "sections": [
                {
                    "sections": [
                        {
                            "type": "LEC",
                            "classUniqueId": {"classNumber": 1},
                            "instructors": [person],
                        },
                        {
                            "type": "DIS",
                            "classUniqueId": {"classNumber": 2},
                            "instructors": [
                                {"name": "Teaching Assistant", "netid": "ta"}
                            ],
                        },
                    ]
                }
            ],
        }
        old = {**current, "term": "1264"}

        class Store:
            db = DB()

            def run(self, run):
                return {"semester": "1272"}

            def records(self, run, kind):
                return {
                    "terms": {"1272": {"name": "Fall 2026"}},
                    "offerings": {"one": current, "cross_listing": current, "old": old},
                    "grades": {},
                }[kind]

        class Base:
            reviews = {}

            def resolve(self, key):
                return key if key == "COMPSCI 300" else None

        context = StudentContext(Store(), "run", Base()).get("COMPSCI 300")
        self.assertEqual(
            [p["name"] for p in context["current_instructors"]], ["Jane Doe"]
        )
        self.assertEqual(context["term_id"], "1272")
        self.assertEqual(context["historical_reviews"], [])
