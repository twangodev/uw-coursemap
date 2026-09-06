import unittest

from name_matcher import NameIndex, find_best_name_match, iter_name_matches


class NameIndexTests(unittest.TestCase):
    def test_index_preserves_exhaustive_matcher_scores_and_ties(self):
        candidates = [
            "John A. Smith",
            "John B. Smith",
            "Jane Smith",
            "Jose García",
            "Anne O'Brien",
            "Xiaoming Li",
            "Mary Smith-Jones",
            "Robert Brown",
            "Cher",
        ]
        index = NameIndex(candidates)
        for query in [
            *candidates,
            "John Smith",
            "J Smith",
            "Jose Garcia",
            "Anne OBrien",
            "Smith, Jane",
            "Bob Brown",
            "Mary Smith",
            "Unknown Person",
            "",
            "Cher",
        ]:
            with self.subTest(query=query):
                self.assertEqual(
                    index.match(query), find_best_name_match(query, candidates)
                )

    def test_process_batches_match_serial_results(self):
        candidates = ["Jane Example", "John Smith", "Jose García"]
        queries = [f"Person{i} Smith" for i in range(520)] + candidates
        expected = dict(iter_name_matches(queries, candidates, workers=1))
        self.assertEqual(
            dict(iter_name_matches(queries, candidates, workers=2)), expected
        )

    def test_malformed_historical_name_has_stable_safe_identifier(self):
        from pathvalidate import validate_filename
        from sanitization import sanitize_instructor_id

        first = sanitize_instructor_id("ADELA OLIVA CH?VEZ")
        validate_filename(first)
        self.assertEqual(first, sanitize_instructor_id("ADELA OLIVA CH?VEZ"))
        self.assertNotEqual(first, sanitize_instructor_id("ADELA OLIVA CH*VEZ"))
        self.assertEqual(sanitize_instructor_id("Jane Example"), "JANE_EXAMPLE")
        self.assertIsNone(sanitize_instructor_id(""))
