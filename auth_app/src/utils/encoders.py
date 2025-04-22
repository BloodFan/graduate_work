from uuid import UUID

from dramatiq.encoder import JSONEncoder


class UUIDEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (list, tuple)):
            return [self.default(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self.default(v) for k, v in obj.items()}
        return super().default(obj)
