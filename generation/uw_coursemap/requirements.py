"""Validate model-produced prerequisite graphs without changing source rules."""

import re


def restore_quotes(value, payload):
    """Resolve whitespace-equivalent quotes back to literal source substrings."""
    text = payload.get("requirements_text") or ""
    for node in value["nodes"]:
        for field in ("evidence", "condition"):
            quote = node[field]
            if not quote or quote in text:
                continue
            parts = re.split(r"(\s+)", quote)
            pattern = "".join(
                r"\s+" if part.isspace() else re.escape(part) for part in parts
            )
            match = re.search(pattern, text)
            if match:
                node[field] = match.group()


def validate_graph(value, payload):
    text = payload.get("requirements_text") or ""
    nodes = value["nodes"]
    if value["status"] == "none":
        if text.strip().lower().rstrip(".") not in {
            "",
            "none",
            "no prerequisites",
            "no requisites",
        }:
            raise ValueError("Nonempty requirements cannot be discarded")
        if nodes or value["root"] is not None:
            raise ValueError("No-requirements result must have an empty graph")
        return
    if value["status"] == "needs_review" and not value["notes"]:
        raise ValueError("Review status requires an explanation")
    by_id = {node["id"]: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("Duplicate requirement node ID")
    if not nodes and value["status"] == "needs_review" and value["root"] is None:
        return
    if value["root"] not in by_id:
        raise ValueError("Missing requirement root")
    linked = {
        (tuple(sorted(ref["subjects"])), ref["course_number"])
        for ref in payload.get("linked_courses", [])
    }
    for node in nodes:
        if not node["evidence"] or node["evidence"] not in text:
            raise ValueError("Requirement evidence must quote the source")
        kind, children = node["kind"], node["children"]
        if len(children) != len(set(children)) or any(
            child not in by_id for child in children
        ):
            raise ValueError("Invalid requirement child references")
        if kind in {"all", "any"} and len(children) < 2:
            raise ValueError("Boolean groups require at least two children")
        if kind == "not" and len(children) != 1:
            raise ValueError("Negation requires one child")
        if kind in {"course", "condition"} and children:
            raise ValueError("Requirement leaves cannot have children")
        if kind == "course":
            course = node["course"]
            if (
                course is None
                or (tuple(sorted(course["subjects"])), course["course_number"])
                not in linked
            ):
                raise ValueError("Course requirement is absent from the source links")
            if node["condition"] is not None:
                raise ValueError("Course node must not hide a separate condition")
        elif node["course"] is not None:
            raise ValueError("Only course nodes may carry course references")
        if kind == "condition":
            if not node["condition"] or node["condition"] not in text:
                raise ValueError(
                    "Non-course conditions must preserve verbatim source text"
                )
        elif node["condition"] is not None:
            raise ValueError("Only condition nodes may carry conditions")
    visited, active = set(), set()

    def visit(key):
        if key in active:
            raise ValueError("Requirement graph contains a cycle")
        if key in visited:
            raise ValueError("Requirement graph must be a tree")
        active.add(key)
        for child in by_id[key]["children"]:
            visit(child)
        active.remove(key)
        visited.add(key)

    visit(value["root"])
    if visited != set(by_id):
        raise ValueError("Requirement graph has unreachable nodes")
