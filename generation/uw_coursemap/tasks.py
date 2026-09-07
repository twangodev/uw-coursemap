"""Resolve task assets into the immutable prompt and schema stored with each job."""

import json
from pathlib import Path


def load_task(path):
    path = Path(path)
    task = json.loads(path.read_text())
    if "prompt_files" in task:
        if "prompt" in task:
            raise ValueError("Task must use prompt or prompt_files, not both")
        files = task.pop("prompt_files")
        if (
            not isinstance(files, list)
            or not files
            or not all(isinstance(name, str) and name for name in files)
        ):
            raise ValueError("prompt_files must be a nonempty list of file names")
        task["prompt"] = "\n\n".join(
            (path.parent / name).read_text().strip() for name in files
        )
    if "schema_file" in task:
        if "schema" in task:
            raise ValueError("Task must use schema or schema_file, not both")
        task["schema"] = json.loads((path.parent / task.pop("schema_file")).read_text())
    return task
