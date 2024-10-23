from .networking import ConnectionInfo
from .http.constants import HEADER_DATE_FORMAT
from .http.request import HTTPRequest
from .http.response import HTTPResponse
from datetime import datetime, timezone
from typing import Optional
from abc import ABC, abstractmethod
from pathlib import Path
from math import ceil
import base64

StrPath = str


class RequestHandler(ABC):
    @abstractmethod
    def __call__(
        self, conn_info: ConnectionInfo, request: "HTTPRequest"
    ) -> HTTPResponse: ...


# Parse HTTP header date format
def from_http_date(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, HEADER_DATE_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def to_http_date(value: datetime) -> str:
    return value.strftime(HEADER_DATE_FORMAT)


# Generate nginx-like ETag
def file_etag(path: Path) -> str:
    def int_to_b64(value: int) -> str:
        raw_value = value.to_bytes(max(ceil(value.bit_length() / 8), 1))
        return base64.b64encode(raw_value).decode()

    stat = Path(path).stat()
    return f'W/"{int_to_b64(stat.st_size)}-{int_to_b64(stat.st_mtime_ns)}"'
