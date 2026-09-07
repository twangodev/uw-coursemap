"""Validate model-produced prerequisite graphs without changing source rules."""

import re


def shared_subject_references(payload):
    """Resolve only explicit comma-list shorthand, retaining literal source spans."""
    text = payload.get("requirements_text") or ""
    subjects = {s for ref in payload.get("linked_courses", []) for s in ref["subjects"]}
    result = []
    for subject in sorted(subjects):
        prefix = r"\s*".join(re.escape(c) for c in subject.replace(" ", ""))
        pattern = rf"(?<![A-Za-z]){prefix}\s*\d{{3}}(?P<tail>(?:\s*,\s*(?:or\s+)?\d{{3}})+)(?!\d)"
        for match in re.finditer(pattern, text, re.I):
            for number in re.finditer(r"\d{3}", match["tail"]):
                start = match.start("tail") + number.start()
                result.append(
                    {
                        "subject": subject,
                        "course_number": int(number.group()),
                        "text": number.group(),
                        "start": start,
                        "end": start + 3,
                        "context": match.group(),
                    }
                )
    return result


def ambiguous_semicolons(text):
    """Bare top-level semicolons do not specify AND versus OR."""
    depth, cuts = 0, []
    for i, char in enumerate(text):
        depth += (char == "(") - (char == ")")
        if char == ";" and depth == 0:
            cuts.append(i)
    return any(
        not re.match(r"\s*(?:and\b|or\b|not open\b)", text[i + 1 :], re.I) for i in cuts
    )


def restore_quotes(value, payload):
    """Resolve case and whitespace differences back to literal source substrings."""
    text = payload.get("requirements_text") or ""
    shorthand = shared_subject_references(payload)
    for node in value["nodes"]:
        for field in ("evidence", "condition"):
            quote = node[field]
            if not quote or quote in text:
                continue
            candidates = [quote]
            if quote.endswith(".") and quote[:-1]:
                candidates.append(quote[:-1])
            for candidate in candidates:
                parts = re.split(r"(\s+)", candidate)
                pattern = "".join(
                    r"\s+" if part.isspace() else re.escape(part) for part in parts
                )
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    node[field] = match.group()
                    break
            if node[field] not in text:
                compact = re.sub(r"\s+", "", node[field]).upper()
                matches = [
                    r
                    for r in shorthand
                    if compact
                    == r["subject"].replace(" ", "").upper() + str(r["course_number"])
                ]
                if len(matches) == 1:
                    node[field] = matches[0]["text"]
                    if node["kind"] != "condition":
                        continue
                    value["status"] = "needs_review"
                    note = f"Source shorthand {matches[0]['text']} inherits {matches[0]['subject']}; its catalog identity requires review."
                    if note not in value["notes"] and len(value["notes"]) < 4:
                        value["notes"].append(note)
        if (
            node["kind"] == "condition"
            and node["condition"] is None
            and node["evidence"] == text
            and text.strip()
        ):
            node["condition"] = text


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
    source_numbers = set(re.findall(r"(?<!\d)\d{3}(?!\d)", text))
    represented = " ".join(
        str(node["course"]["course_number"])
        if node["kind"] == "course"
        else node["condition"] or ""
        for node in nodes
        if not node["children"]
    )
    missing = source_numbers - set(re.findall(r"(?<!\d)\d{3}(?!\d)", represented))
    if missing:
        raise ValueError(
            f"Source numeric references missing from leaf conditions: {', '.join(sorted(missing))}. "
            "Preserve every alternative. References absent from linked_courses must remain verbatim condition nodes with needs_review, not be dropped."
        )
    if value["status"] == "parsed":
        # A separate exclusion sentence constrains all eligibility alternatives.
        # This deliberately covers one explicit catalog form, not arbitrary prose.
        clauses = re.findall(
            r"(?:^|[.!?]\s+)(Not open to students with credit for[^.!?]+)",
            text,
            flags=re.IGNORECASE,
        )
        unconditional = []

        def exclusions(key):
            node = by_id[key]
            if node["kind"] == "not":
                unconditional.append(node["evidence"].rstrip(". "))
            elif node["kind"] == "all":
                for child in node["children"]:
                    exclusions(child)

        exclusions(value["root"])
        for clause in clauses:
            if not any(clause in evidence for evidence in unconditional):
                raise ValueError(
                    "Standalone credit exclusion must apply to every eligibility alternative: "
                    "use an unconditional not node under the root all (or root not), "
                    "quoting the entire exclusion sentence as its evidence"
                )


def graph_diagnostics(value, payload):
    """Collect repairable faults together, even when the candidate is cyclic."""
    text = payload.get("requirements_text") or ""
    nodes = value["nodes"]
    by_id = {n["id"]: n for n in nodes}
    errors = []
    if len(by_id) != len(nodes):
        errors.append("Duplicate node IDs; assign a unique ID to each node.")
    if nodes and value["root"] not in by_id:
        errors.append(f"Missing root node {value['root']!r}.")
    for node in nodes:
        key = node["id"]
        if not node["evidence"] or node["evidence"] not in text:
            errors.append(
                f"Node {key}: evidence {node['evidence']!r} must quote an exact source substring."
            )
        if node["kind"] == "course":
            course = node["course"]
            allowed = payload.get("linked_courses", [])
            if course is None or not any(
                set(course["subjects"]) == set(ref["subjects"])
                and course["course_number"] == ref["course_number"]
                for ref in allowed
            ):
                errors.append(
                    f"Node {key}: course {course!r} is absent from the source links (linked_courses). "
                    "Standing, declared programs, and subject credit counts are condition nodes, not courses. "
                    "Never invent course 0. For a source reference absent from linked_courses, use kind=condition, "
                    "course=null, condition=<verbatim source clause>, children=[], and needs_review with an explanatory note. "
                    f"Allowed course references: {allowed!r}."
                )
        if node["kind"] == "condition" and (
            not node["condition"] or node["condition"] not in text
        ):
            errors.append(
                f"Node {key}: condition {node['condition']!r} must be a nonempty literal source substring. "
                f"Its evidence is {node['evidence']!r}; copy the relevant source clause into condition, "
                "without adding or removing a negation or standing qualifier."
            )
        if key in node["children"]:
            errors.append(f"Node {key} references itself; remove the self-reference.")
        missing = set(node["children"]) - by_id.keys()
        if missing:
            errors.append(
                f"Node {key} references missing nodes: {', '.join(sorted(missing))}."
            )
    visited, active = set(), set()

    def visit(key):
        if key not in by_id:
            return
        if key in active:
            errors.append(
                f"Cycle reaches node {key}; requirement graphs must be trees."
            )
            return
        if key in visited:
            errors.append(
                f"Node {key} has multiple parents; requirement graphs must be trees."
            )
            return
        visited.add(key)
        active.add(key)
        for child in by_id[key]["children"]:
            visit(child)
        active.remove(key)

    visit(value["root"])
    unreachable = by_id.keys() - visited
    if unreachable:
        errors.append(
            f"Unreachable nodes: {', '.join(sorted(unreachable))}; connect all conditions and exclusions to the root."
        )
    clauses = re.findall(
        r"(?:^|[.!?]\s+)(Not open to students with credit for[^.!?]+)",
        text,
        flags=re.IGNORECASE,
    )
    unconditional, seen = [], set()

    def exclusions(key):
        if key in seen or key not in by_id:
            return
        seen.add(key)
        node = by_id[key]
        if node["kind"] == "not":
            unconditional.append(node["evidence"])
        elif node["kind"] == "all":
            for child in node["children"]:
                exclusions(child)

    exclusions(value["root"])
    for clause in clauses:
        if not any(clause in evidence for evidence in unconditional):
            errors.append(
                f"Missing global exclusion {clause!r}: use a not node under the root all (or root not), with the full exclusion as evidence, applying to every eligibility alternative."
            )
    return errors
