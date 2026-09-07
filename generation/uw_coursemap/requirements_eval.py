"""Compare requirement expressions, ignoring node IDs and associative ordering."""

import json


def expression(value):
    nodes = {node["id"]: node for node in value["nodes"]}

    def visit(key):
        node = nodes[key]
        if node["kind"] in {"course", "condition"}:
            return {node["kind"]: node[node["kind"]]}
        return {node["kind"]: [visit(child) for child in node["children"]]}

    return visit(value["root"]) if value["root"] is not None else None


def normalize(value):
    if value is None:
        return None
    kind, item = next(iter(value.items()))
    if kind == "condition":
        return {kind: " ".join(item.split()).rstrip(".")}
    if kind == "course":
        item = {**item, "subjects": sorted(item["subjects"])}
        if item["timing"] == "prior_or_concurrent":
            return normalize(
                {
                    "any": [
                        {"course": {**item, "timing": timing}}
                        for timing in ["prior", "concurrent"]
                    ]
                }
            )
        return {kind: item}
    children = []
    for child in item:
        child = normalize(child)
        children.extend(
            child[kind] if kind in {"any", "all"} and kind in child else [child]
        )
    if kind in {"any", "all"}:
        unique = {json.dumps(child, sort_keys=True): child for child in children}
        children = [unique[key] for key in sorted(unique)]
        if len(children) == 1:
            return children[0]
    return {kind: children}


def matches(case, value):
    return value["status"] == case["expected_status"] and normalize(
        expression(value)
    ) == normalize(case["expected_expression"])
