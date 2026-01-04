"""Requirement Abstract Syntax Tree Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class Leaf(BaseModel):
    """A leaf node in the requirement AST - either text or a course reference."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: str | Any  # str or CourseReference

    @field_serializer("payload")
    def serialize_payload(self, payload: str | Any) -> str | dict:
        """Serialize the payload."""
        if isinstance(payload, str):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        if hasattr(payload, "to_dict"):
            return payload.to_dict()
        return str(payload)

    def model_dump(self, **kwargs) -> str | dict:
        """Override to return just the payload, not wrapped in an object."""
        return self.serialize_payload(self.payload)

    def to_tree_print(self) -> str:
        return _tree_repr(self, is_root=True)


class Node(BaseModel):
    """A node in the requirement AST with an operator and children."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    operator: str  # "AND" or "OR"
    children: list["Node | Leaf"]

    @field_serializer("children")
    def serialize_children(self, children: list["Node | Leaf"]) -> list:
        """Serialize children recursively."""
        result = []
        for child in children:
            if isinstance(child, Node):
                result.append(child.model_dump())
            elif isinstance(child, Leaf):
                result.append(child.model_dump())
            else:
                result.append(str(child))
        return result

    def to_tree_print(self) -> str:
        return _tree_repr(self, is_root=True)


class RequirementAbstractSyntaxTree(BaseModel):
    """The root of a requirement AST."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    root: Node | Leaf

    @field_serializer("root")
    def serialize_root(self, root: Node | Leaf) -> dict | str:
        """Serialize the root node."""
        return root.model_dump()

    def model_dump(self, **kwargs) -> dict | str:
        """Override to return just the root, not wrapped in an object."""
        return self.serialize_root(self.root)

    def to_tree_print(self) -> str:
        return _tree_repr(self.root, is_root=True)

    def course_combinations(self) -> list[list]:
        """Get all possible course combinations that satisfy the requirements."""

        def _recurse(node: Node | Leaf) -> list[list]:
            if isinstance(node, Leaf):
                if not isinstance(node.payload, str):
                    return [[node.payload]]
                else:
                    return [[]]

            assert isinstance(node, Node)
            if node.operator == "AND":
                combos = [[]]
                for child in node.children:
                    child_combos = _recurse(child)
                    combos = [prev + curr for prev in combos for curr in child_combos]
                return combos

            elif node.operator == "OR":
                combos = []
                for child in node.children:
                    combos.extend(_recurse(child))
                return combos

            else:
                raise ValueError(f"Unknown operator {node.operator!r}")

        raw = _recurse(self.root)
        nonempty = [combo for combo in raw if combo]
        seen = set()
        unique = []
        for combo in nonempty:
            key = tuple(sorted(combo, key=lambda cr: str(cr)))
            if key not in seen:
                seen.add(key)
                unique.append(combo)
        return unique


def _tree_repr(
    node: Node | Leaf,
    prefix: str = "",
    is_last: bool = True,
    is_root: bool = False,
) -> str:
    """Create a tree representation string for debugging."""
    if is_root:
        label = node.operator if isinstance(node, Node) else node.payload
        line = str(label)
        children_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        label = node.operator if isinstance(node, Node) else node.payload
        line = f"{prefix}{connector}{label}"
        children_prefix = prefix + ("    " if is_last else "│   ")

    if isinstance(node, Node):
        lines = [line]
        for idx, child in enumerate(node.children):
            last = idx == len(node.children) - 1
            lines.append(_tree_repr(child, children_prefix, last))
        return "\n".join(lines)
    else:
        return line


# Rebuild models for forward references
Node.model_rebuild()
RequirementAbstractSyntaxTree.model_rebuild()
