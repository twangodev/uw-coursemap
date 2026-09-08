"""Serializable model profiles shared by clients and server launchers."""

import json
import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field


class ModelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(min_length=1)
    revision: str | None = None
    base_url: str
    runner: str = "generate"
    context_length: int = Field(default=8192, ge=256)
    max_output_tokens: int = Field(default=2048, ge=1)
    concurrency: int = Field(default=2, ge=1, le=512)
    temperature: float = Field(default=0.2, ge=0, le=2)
    top_p: float = Field(default=0.95, gt=0, le=1)
    top_k: int = Field(default=20, ge=0)
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    thinking: bool = False
    request_timeout_seconds: int = Field(default=180, ge=1, le=1800)
    document_prefix: str = ""
    engine: str = "vllm"
    engine_version: str = "0.28.0"
    dimensions: int | None = Field(default=None, ge=1)
    server_args: list[str] = Field(default_factory=list)

    @property
    def served_model(self):
        return f"{self.model}@{self.revision}"


def load_profile(path, name, resolve=True):
    content = Path(path).read_text()
    profiles = (
        json.loads(content) if Path(path).suffix == ".json" else tomllib.loads(content)
    )
    profile = ModelProfile.model_validate(profiles["profiles"][name])
    url = urlparse(profile.base_url)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError("Use an HTTP API URL without credentials, query, or fragment")
    if profile.runner not in {"pooling", "generate"}:
        raise ValueError("runner must be pooling or generate")
    if (
        profile.max_output_tokens >= profile.context_length
        and profile.runner == "generate"
    ):
        raise ValueError("Output token limit must leave room for the input")
    if resolve and not (
        profile.revision and re.fullmatch("[0-9a-f]{40}", profile.revision)
    ):
        from huggingface_hub import HfApi

        profile.revision = (
            HfApi().model_info(profile.model, revision=profile.revision).sha
        )
    if not profile.revision or not re.fullmatch("[0-9a-f]{40}", profile.revision):
        raise ValueError("Profile must resolve to an immutable model commit")
    return profile


def lock_profiles(path, names, output):
    """Resolve once, then share the same immutable identities with all clients."""
    from .models import canonical

    target = Path(output)
    if target.suffix != ".json":
        raise ValueError("Locked model profiles require a .json output path")
    data = {"profiles": {name: load_profile(path, name).model_dump() for name in names}}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(canonical(data))
    temporary.replace(target)
    return {"models_config": str(target), "profiles": list(data["profiles"])}
