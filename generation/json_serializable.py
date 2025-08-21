import json


class JsonSerializable:
    @classmethod
    def from_json(cls, json_data) -> "JsonSerializable":
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())
