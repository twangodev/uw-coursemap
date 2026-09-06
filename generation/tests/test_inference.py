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
