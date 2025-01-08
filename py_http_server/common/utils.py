from .constants import HEADER_DATE_FORMAT
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from math import ceil
import base64


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
