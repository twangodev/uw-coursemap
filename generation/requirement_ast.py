import re
from typing import Union

from json_serializable import JsonSerializable

token_specs = [
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\bAND\b', 'AND'),
    (r'\bOR\b', 'OR'),
]

tokenizer_regex = '|'.join(f'(?P<{name}>{pattern})' for pattern, name in token_specs)
tokenizer_re = re.compile(tokenizer_regex, re.IGNORECASE)

def tokenize_requisites(linked_requisite_text):
    from course import Course
    tokens = []

    for piece in linked_requisite_text:
        if isinstance(piece, Course.Reference):
            tokens.append(('COURSE', piece))
            continue

        position = 0
        for match in tokenizer_re.finditer(piece):
            if position < match.start():
                tokens.append(('TEXT', piece[position:match.start()]))

            token_type = match.lastgroup
            token_value = match.group(token_type)

            tokens.append((token_type, token_value))
            position = match.end()

        if position < len(piece):
            tokens.append(('TEXT', piece[position:]))


    return tokens

class Leaf:
    def __init__(self, payload: JsonSerializable | str):
        self.payload = payload

    def __repr__(self):
        return f"Leaf({self.payload})"

class Node(JsonSerializable):
    def __init__(self, operator: str, children: list[Union['Node', Leaf]]):
        self.operator = operator
        self.children = children

    def __repr__(self):
        return f"Node({self.operator}, {self.children})"

    def to_dict(self):
        return {
            "operator": self.operator,
            "children": [child.to_dict() if isinstance(child, JsonSerializable) else str(child) for child in self.children]
        }

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

    # @classmethod
    # def from_linked_requisite_text(cls, ) -> 'RequirementAbstractSyntaxTree':