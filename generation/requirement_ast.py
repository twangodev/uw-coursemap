import re
from typing import Union

from json_serializable import JsonSerializable

token_specs = [
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\bAND\b', 'AND'),
    (r'\bOR\b|;', 'OR'),
    (r'\,', 'COMMA'),
]

leaf_like = {'TEXT', 'COURSE'}

tokenizer_regex = '|'.join(f'(?P<{name}>{pattern})' for pattern, name in token_specs)
tokenizer_re = re.compile(tokenizer_regex, re.IGNORECASE)

def infer_commas(tokens):
    """
    Infers the commas in the tokenized list of requisites.
    For example, if the tokens are:
    [('COURSE', 'CS101'), ('COMMA', ','), ('COURSE', 'CS102'), ('AND', 'AND'), ('COURSE', 'CS103')],
    it will infer that the comma is an AND operator.
    The output will be:
    [('COURSE', 'CS101'), ('AND', ','), ('COURSE', 'CS102'), ('AND', 'AND'), ('COURSE', 'CS103')].
    """
    inferred_tokens = []

    for i, (kind, value) in enumerate(tokens):
        if kind != 'COMMA':
            inferred_tokens.append((kind, value))
            continue

        depth = 0
        assumed_operator = 'AND'
        for next_kind, next_value in tokens[i + 1:]:
            if next_kind == 'LPAREN':
                depth += 1
            elif next_kind == 'RPAREN':
                depth -= 1

            if next_kind in ('AND', 'OR') and depth == 0:
                assumed_operator = next_kind
                break

        inferred_tokens.append((assumed_operator, value))

    return inferred_tokens

def collapse_operators(tokens):
    """
    Collapses consecutive AND/OR operators into a single operator.
    For example, if the tokens are:
    [('AND', 'AND'), ('AND', 'AND'), ('COURSE', 'CS101')],
    it will collapse the ANDs into a single AND.
    The output will be:
    [('AND', 'AND'), ('COURSE', 'CS101')].
    """
    out = []
    last_operator = None

    for kind, value in tokens:
        if kind in ('AND', 'OR'):
            if last_operator != kind:
                out.append((kind, value))
                last_operator = kind
        else:
            out.append((kind, value))
            last_operator = None

    return out

def hoist_group_operators(tokens):
    out = []
    i = 0
    while i < len(tokens):
        kind, val = tokens[i]
        if kind == 'LPAREN' and i + 1 < len(tokens) and tokens[i+1][0] in ('AND','OR'):
            op_kind, op_val = tokens[i+1]
            if out and out[-1][0] not in ('LPAREN','AND','OR'):
                out.append((op_kind, op_val))
            out.append((kind, val))
            i += 2
        else:
            out.append((kind, val))
            i += 1
    return out

def tokenize_requisites(linked_requisite_text):
    from course import Course
    tokens = []

    for piece in linked_requisite_text:
        if isinstance(piece, Course.Reference):
            tokens.append(('COURSE', piece))
            continue

        position = 0
        for match in tokenizer_re.finditer(piece):
            if position < match.start() and piece[position:match.start()].strip():
                tokens.append(('TEXT', piece[position:match.start()].strip()))

            token_type = match.lastgroup
            token_value = match.group(token_type)

            tokens.append((token_type, token_value))
            position = match.end()

        if position < len(piece) and piece[position:].strip():
            tokens.append(('TEXT', piece[position:].strip()))

    tokens = infer_commas(tokens)
    tokens = hoist_group_operators(tokens)
    tokens = collapse_operators(tokens)
    return tokens

class Leaf(JsonSerializable):
    def __init__(self, payload: JsonSerializable | str):
        self.payload = payload

    def to_tree_print(self):
        return _tree_repr(self, is_root=True)

    def to_dict(self):
        if isinstance(self.payload, JsonSerializable):
            return self.payload.to_dict()
        return str(self.payload)

class Node(JsonSerializable):
    def __init__(self, operator: str, children: list[Union['Node', Leaf]]):
        self.operator = operator
        self.children = children

    def to_dict(self):
        return {
            "operator": self.operator,
            "children": [child.to_dict() if isinstance(child, JsonSerializable) else str(child) for child in self.children]
        }

    def to_tree_print(self):
        return _tree_repr(self, is_root=True)

def _tree_repr(node: Union[Node, Leaf],
               prefix: str = "",
               is_last: bool = True,
               is_root: bool = False) -> str:
    if is_root:
        label = node.operator if isinstance(node, Node) else node.payload
        line = label
        children_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        label = node.operator if isinstance(node, Node) else node.payload
        line = f"{prefix}{connector}{label}"
        children_prefix = prefix + ("    " if is_last else "│   ")

    if isinstance(node, Node):
        lines = [line]
        for idx, child in enumerate(node.children):
            last = (idx == len(node.children) - 1)
            lines.append(_tree_repr(child, children_prefix, last))
        return "\n".join(lines)
    else:
        return line

class RequirementAbstractSyntaxTree(JsonSerializable):

    def __init__(self, root: Union[Node, Leaf]):
        self.root = root

    @classmethod
    def from_json(cls, json_data):
        if isinstance(json_data, dict):
            return cls(Node.from_json(json_data))
        elif isinstance(json_data, str):
            return cls(Leaf(json_data))
        else:
            raise ValueError("Invalid JSON data for RequirementAbstractSyntaxTree")

    def to_dict(self):
        return self.root.to_dict() if isinstance(self.root, JsonSerializable) else str(self.root)

    def to_tree_print(self):
        return _tree_repr(self.root, is_root=True)

class RequirementParser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> RequirementAbstractSyntaxTree:
        root = self.parse_or()
        return RequirementAbstractSyntaxTree(root)

    def parse_or(self):
        children = [self.parse_and()]
        while self._peek_kind() == 'OR':
            self.pos += 1
            children.append(self.parse_and())
        return children[0] if len(children) == 1 else Node('OR', children)

    def parse_and(self):
        children = [self.parse_primary()]

        while True:
            kind = self._peek_kind()
            if kind == 'AND':
                self.pos += 1
                children.append(self.parse_primary())
            elif kind in ('TEXT', 'COURSE', 'LPAREN'):
                children.append(self.parse_primary())
            else:
                break

        return children[0] if len(children) == 1 else Node('AND', children)

    def parse_primary(self):
        kind = self._peek_kind()

        if kind == 'LPAREN':
            self.pos += 1
            node = self.parse_or()
            if self._peek_kind() != 'RPAREN':
                raise SyntaxError("Expected ')'")
            self.pos += 1
            return node

        if kind in ('TEXT', 'COURSE'):
            _, val = self.tokens[self.pos]
            self.pos += 1
            return Leaf(val)

        raise SyntaxError(f"Unexpected token {kind!r}")

    def _peek_kind(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else 'EOF'