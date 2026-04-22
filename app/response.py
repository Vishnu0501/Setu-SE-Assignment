import json
from decimal import Decimal
from datetime import datetime, date

from fastapi.responses import JSONResponse


class AppJSONResponse(JSONResponse):
    """Custom response class that serializes Decimal and datetime types."""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            default=self._encoder,
            ensure_ascii=False,
        ).encode("utf-8")

    @staticmethod
    def _encoder(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not JSON serializable")