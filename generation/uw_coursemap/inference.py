"""Inference client for a separately managed local vLLM pooling server."""

import os
import json
import re

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class EmbeddingClient:
    def __init__(self, model, revision, base_url, max_tokens=512, dimensions=None):
        if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(
                "Inference requires an immutable Hugging Face commit revision"
            )
        self.model_name = f"vllm-0.28.0-mean-normalized-v1/{model}"
        self.max_tokens = max_tokens
        self.dimensions = dimensions
        self.pipeline_revision = revision
        self.served_model = f"{model}@{revision}"
        self.base_url = base_url.rstrip("/")

    def encode(self, sentences, **kwargs):
        single = isinstance(sentences, str)
        texts = [sentences] if single else list(sentences)
        if not texts:
            raise ValueError("Embedding input must not be empty")
        texts = [getattr(self, "prefix", "") + text for text in texts]
        output = []
        with requests.Session() as session:
            retry = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"],
            )
            session.mount("http://", HTTPAdapter(max_retries=retry))
            session.mount("https://", HTTPAdapter(max_retries=retry))
            token = os.environ.get("COURSEMAP_INFERENCE_API_KEY")
            if token:
                session.headers["Authorization"] = f"Bearer {token}"
            for offset in range(0, len(texts), 32):
                batch = texts[offset : offset + 32]
                response = session.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "model": self.served_model,
                        "input": batch,
                        "encoding_format": "float",
                        "truncate_prompt_tokens": self.max_tokens,
                    },
                    timeout=(10, 120),
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("model") != self.served_model:
                    raise ValueError(
                        "Inference server returned a different model identity"
                    )
                data = sorted(payload["data"], key=lambda item: item["index"])
                if [item["index"] for item in data] != list(range(len(batch))):
                    raise ValueError("Incomplete or duplicate embedding response")
                vectors = np.asarray(
                    [item["embedding"] for item in data], dtype=np.float32
                )
                if (
                    vectors.ndim != 2
                    or not vectors.shape[1]
                    or not np.isfinite(vectors).all()
                ):
                    raise ValueError("Invalid embedding vectors")
                if self.dimensions and vectors.shape[1] != self.dimensions:
                    raise ValueError("Unexpected embedding dimension")
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                if (norms == 0).any():
                    raise ValueError("Zero embedding vector")
                output.extend(vectors / norms)
        result = np.stack(output)
        return result[0] if single else result


def configured_model(kind):
    profiles = json.loads(os.environ.get("COURSEMAP_MODEL_PROFILES", "{}"))
    if kind in profiles:
        from .models import digest

        profile = profiles[kind]
        client = EmbeddingClient(
            profile["model"],
            profile["revision"],
            profile["base_url"],
            max_tokens=profile["context_length"],
            dimensions=profile.get("dimensions"),
        )
        contract = {
            k: v for k, v in profile.items() if k not in {"base_url", "concurrency"}
        }
        client.model_name = "profile-" + digest(contract)
        client.prefix = profile.get("document_prefix", "")
        return client
    if kind == "embedding":
        model = "avsolatorio/GIST-large-Embedding-v0"
        port = 8001
    else:
        model = "sentence-transformers/all-MiniLM-L6-v2"
        port = 8002
    prefix = f"COURSEMAP_{kind.upper()}"
    return EmbeddingClient(
        model,
        os.environ.get(f"{prefix}_REVISION"),
        os.environ.get(f"{prefix}_BASE_URL", f"http://127.0.0.1:{port}/v1"),
        max_tokens=512 if kind == "embedding" else 256,
        dimensions=1024 if kind == "embedding" else 384,
    )
