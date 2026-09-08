import tempfile
from pathlib import Path
import unittest

from uw_coursemap.identities import CourseIdentities


class IdentityTests(unittest.TestCase):
    def test_crosslisting_addition_preserves_id_after_registry_reload(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "identities.json"
            registry = CourseIdentities(path)
            original = registry.identify("COMPSCI 759")
            registry.save()
            registry = CourseIdentities(path)
            self.assertEqual(registry.identify("COMPSCI/ECE 759"), original)
            registry.save()
            self.assertEqual(CourseIdentities(path).identify("ECE 759"), original)

    def test_renumbering_and_conflicting_aliases_do_not_merge(self):
        registry = CourseIdentities()
        cs = registry.identify("COMPSCI 300")
        self.assertNotEqual(registry.identify("COMPSCI 301"), cs)
        ece = registry.identify("ECE 300")
        combined = registry.identify("COMPSCI/ECE 300")
        self.assertNotIn(combined, [cs, ece])
        self.assertEqual(registry.identify("COMPSCI 300"), cs)
        self.assertEqual(registry.identify("ECE 300"), ece)

    def test_instructor_ids_are_source_scoped_and_not_name_matches(self):
        from uw_coursemap.dataset_shape import instructor_identity

        def uid(source, record):
            return instructor_identity(source, record, "scope")["instructor_uid"]

        self.assertEqual(
            uid("enrollment", {"netid": "ABC", "name": "Old"}),
            uid("enrollment", {"netid": "abc", "name": "New"}),
        )
        self.assertNotEqual(
            uid("madgrades", {"id": 1, "name": "Same"}),
            uid("madgrades", {"id": 2, "name": "Same"}),
        )
        self.assertNotEqual(
            uid("madgrades", {"id": "abc", "name": "Same"}),
            uid("enrollment", {"netid": "abc", "name": "Same"}),
        )
        self.assertEqual(
            instructor_identity("legacy", {"name": "Same"}, "scope")["identity_status"],
            "unresolved",
        )
