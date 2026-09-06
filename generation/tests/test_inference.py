import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from uw_coursemap.inference import EmbeddingClient


class InferenceTests(unittest.TestCase):
    def test_api_batches_order_and_validation(self):
        model = EmbeddingClient(
            "test", "a" * 40, "http://127.0.0.1:8001/v1", dimensions=2
        )
        batches = []
        with patch("uw_coursemap.inference.requests.Session") as factory:
            session = factory.return_value.__enter__.return_value

            def respond(url, json, timeout):
                batches.append(json)
                response = unittest.mock.Mock()
                response.json.return_value = {
                    "model": model.served_model,
                    "data": [
                        {"index": i, "embedding": [3, 4]}
                        for i in reversed(range(len(json["input"])))
                    ],
                }
                return response

            session.post.side_effect = respond
            result = model.encode(["text"] * 33)
            self.assertEqual(result.shape, (33, 2))
            np.testing.assert_allclose(result[0], [0.6, 0.8])
            self.assertEqual([len(batch["input"]) for batch in batches], [32, 1])
            self.assertEqual(batches[0]["truncate_prompt_tokens"], 512)
            session.post.side_effect = None
            for payload in [
                {"model": "wrong", "data": []},
                {"model": model.served_model, "data": []},
                {
                    "model": model.served_model,
                    "data": [{"index": 0, "embedding": [0, 0]}],
                },
                {
                    "model": model.served_model,
                    "data": [{"index": 0, "embedding": [float("nan"), 1]}],
                },
            ]:
                session.post.return_value.json.return_value = payload
                with self.assertRaises(ValueError):
                    model.encode("text")

    def test_keyword_backend_never_loads_local_model_and_caches_batches(self):
        from embeddings import CachedKeyBERT

        model = unittest.mock.Mock()
        model.model_name = "test"
        model.pipeline_revision = "a" * 40
        model.encode.side_effect = lambda texts, **kwargs: np.asarray(
            [[1.0, len(text) + 1] for text in texts]
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch(
                "sentence_transformers.SentenceTransformer",
                side_effect=AssertionError("Local inference prohibited"),
            ),
        ):
            keywords = CachedKeyBERT(directory, model)
            first = keywords.extract_keywords(
                "computer science and mathematics", top_n=2
            )
            calls = model.encode.call_count
            second = keywords.extract_keywords(
                "computer science and mathematics", top_n=2
            )
            self.assertEqual(first, second)
            self.assertEqual(model.encode.call_count, calls)

    def test_profile_cache_tracks_embedding_contract(self):
        import json
        from uw_coursemap.inference import configured_model
        from uw_coursemap.profiles import ModelProfile

        profile = ModelProfile(
            model="test",
            revision="a" * 40,
            base_url="http://127.0.0.1:8001/v1",
            runner="pooling",
        ).model_dump()

        def identity(value):
            with patch.dict(
                "os.environ",
                {"COURSEMAP_MODEL_PROFILES": json.dumps({"embedding": value})},
            ):
                return configured_model("embedding").model_name

        base = identity(profile)
        self.assertEqual(
            base, identity({**profile, "base_url": "http://localhost:9000/v1"})
        )
        for key, value in [
            ("document_prefix", "passage: "),
            ("dimensions", 8),
            ("context_length", 4096),
            ("server_args", ["--pooler-config", '{"pooling_type":"LAST"}']),
        ]:
            self.assertNotEqual(base, identity({**profile, key: value}))

    def test_prerequisite_popularity_uses_branch_enrollment(self):
        from types import SimpleNamespace
        from embeddings import score_branch

        def course(reference, enrollment):
            return SimpleNamespace(
                course_reference=reference,
                cumulative_grade_data=SimpleNamespace(total=enrollment),
                get_full_summary=lambda: "same semantic content",
            )

        target, small, large = (
            course("target", 100),
            course("small", 10),
            course("large", 80),
        )
        with patch("embeddings.get_embedding", return_value=np.asarray([1.0, 0.0])):
            args = ("unused", None, target, {"small": small, "large": large})
            self.assertAlmostEqual(score_branch(*args, 100, ["small"], 0, 1), 0.1)
            self.assertAlmostEqual(score_branch(*args, 100, ["large"], 0, 1), 0.8)
            self.assertEqual(score_branch(*args, 0, ["large"], 0, 1), 0)
