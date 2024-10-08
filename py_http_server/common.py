from .networking.address import TCPAddress
from .http.request import HTTPRequest
from .http.response import HTTPResponse
from abc import ABC, abstractmethod
from pathlib import Path
from math import ceil
import base64

StrPath = str


class RequestHandler(ABC):
    @abstractmethod
    def __call__(
        self, requester: TCPAddress, request: "HTTPRequest"
    ) -> HTTPResponse: ...


# Generate nginx-like ETag
def file_etag(path: Path) -> str:
    def int_to_b64(value: int) -> str:
        raw_value = value.to_bytes(max(ceil(value.bit_length() / 8), 1))
        return base64.b64encode(raw_value).decode()

    stat = Path(path).stat()
    return f'W/"{int_to_b64(stat.st_size)}-{int_to_b64(stat.st_mtime_ns)}"'
