"""Data loader with API support and local fallback."""

from __future__ import annotations

import json
import os
from logging import Logger
from pathlib import Path

import requests


class DataLoader:
    """Loads data from public API with local directory fallback."""

    def __init__(
        self,
        logger: Logger,
        api_base_url: str | None = None,
        local_data_dir: str | None = None,
    ):
        self.logger = logger
        self.api_base_url = api_base_url or os.environ.get("PUBLIC_API_URL")
        self.local_data_dir = local_data_dir or os.environ.get("DATA_DIR", "./data")
        self._session = requests.Session()

    def _fetch_from_api(self, path: str) -> dict | None:
        """Fetch JSON from API. Path should not include .json extension."""
        if not self.api_base_url:
            return None

        url = f"{self.api_base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.debug(f"Failed to fetch from API ({url}): {e}")
            return None

    def _read_local_file(self, path: str) -> dict | None:
        """Read JSON from local file. Path should not include .json extension."""
        filepath = Path(self.local_data_dir) / f"{path}.json"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            self.logger.debug(f"Failed to read local file ({filepath}): {e}")
            return None

    def load_json(self, path: str) -> dict | None:
        """
        Load JSON from API first, fallback to local.
        Path should not include .json extension (e.g., 'subjects', 'course/COMPSCI_200').
        """
        # Try API first
        data = self._fetch_from_api(path)
        if data is not None:
            return data

        # Fallback to local
        data = self._read_local_file(path)
        if data is not None:
            return data

        self.logger.warning(f"Could not load data from API or local: {path}")
        return None

    def get_manifest(self) -> dict | None:
        """Fetch the manifest file which lists all available resources."""
        return self.load_json("manifest")

    def load_from_manifest(self, resource_type: str, ids: list[str], path_prefix: str) -> dict[str, dict]:
        """
        Load resources listed in the manifest.

        Args:
            resource_type: Type of resource (for logging)
            ids: List of resource IDs from manifest
            path_prefix: Path prefix for each resource (e.g., 'course', 'instructors')

        Returns:
            Dict mapping resource ID to data
        """
        result = {}
        for resource_id in ids:
            path = f"{path_prefix}/{resource_id}"
            data = self.load_json(path)
            if data is not None:
                result[resource_id] = data
        return result

    def load_directory(self, dir_path: str, manifest_key: str | None = None) -> dict[str, dict]:
        """
        Load all JSON files from a directory.
        Uses manifest if available, otherwise falls back to local directory listing.
        Returns dict mapping filename (without .json) to data.
        """
        result = {}

        # Try to use manifest first
        if manifest_key:
            manifest = self.get_manifest()
            if manifest and manifest_key in manifest:
                return self.load_from_manifest(manifest_key, manifest[manifest_key], dir_path)

        # Fallback to local directory listing
        local_dir = Path(self.local_data_dir) / dir_path
        if not local_dir.exists():
            self.logger.warning(f"Local directory not found: {local_dir}")
            return result

        for filepath in local_dir.glob("*.json"):
            filename = filepath.stem  # filename without .json
            full_path = f"{dir_path}/{filename}"

            # Try API first for each file, fallback to local
            data = self.load_json(full_path)
            if data is not None:
                result[filename] = data

        return result

    def get_subjects(self) -> dict[str, str]:
        """Load subjects mapping."""
        data = self.load_json("subjects")
        if data:
            self.logger.info(f"Loaded {len(data)} subjects.")
        return data or {}

    def get_instructors(self) -> dict[str, dict]:
        """Load all instructors."""
        instructors = self.load_directory("instructors", manifest_key="instructors")
        self.logger.info(f"Loaded {len(instructors)} instructors.")

        return {
            instructor_id: {
                "name": instructor_data["name"],
                "official_name": instructor_data["official_name"],
                "email": instructor_data["email"],
                "position": instructor_data["position"],
                "department": instructor_data["department"],
            }
            for instructor_id, instructor_data in instructors.items()
        }

    def get_courses(self, subjects: dict[str, str]) -> dict[str, dict]:
        """Load all courses."""
        courses = self.load_directory("course", manifest_key="courses")
        self.logger.info(f"Loaded {len(courses)} courses.")

        return {
            course_id: {
                "course_reference": self._process_course_reference(
                    course_data["course_reference"]
                ),
                "course_number": course_data["course_reference"]["course_number"],
                "course_title": course_data["course_title"],
                "subjects": course_data["course_reference"]["subjects"],
                "departments": [
                    subjects.get(shorthand, shorthand)
                    for shorthand in course_data["course_reference"]["subjects"]
                ],
            }
            for course_id, course_data in courses.items()
        }

    def get_random_courses(self, num_courses: int = 5) -> dict[str, dict]:
        """Get random courses from the dataset."""
        import random

        # Try to get course list from manifest first
        manifest = self.get_manifest()
        if manifest and "courses" in manifest:
            course_ids = manifest["courses"]
        else:
            # Fallback to local directory listing
            local_dir = Path(self.local_data_dir) / "course"
            if not local_dir.exists():
                self.logger.warning(f"Course directory not found and no manifest available")
                return {}
            course_ids = [f.stem for f in local_dir.glob("*.json")]

        num_courses = min(num_courses, len(course_ids))
        random_ids = random.sample(course_ids, num_courses)

        result = {}
        for course_id in random_ids:
            data = self.load_json(f"course/{course_id}")
            if data:
                result[course_id] = {
                    "course_reference": self._process_course_reference(
                        data["course_reference"]
                    ),
                    "course_number": data["course_reference"]["course_number"],
                    "course_title": data["course_title"],
                    "subjects": data["course_reference"]["subjects"],
                }

        return result

    @staticmethod
    def _process_course_reference(course_reference: dict) -> str:
        course_number = course_reference["course_number"]
        subjects = sorted(course_reference["subjects"])
        return f"{'/'.join(subjects)} {course_number}"
