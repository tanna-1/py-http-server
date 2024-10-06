from .networking.address import TCPAddress
from .http.request import HTTPRequest
from .http.response import HTTPResponse
from abc import ABC, abstractmethod
from typing import Union
import os
import hashlib

PathLike = Union[str, bytes, os.PathLike]


class RequestHandler(ABC):
    @abstractmethod
    def __call__(
        self, requester: TCPAddress, request: "HTTPRequest"
    ) -> HTTPResponse: ...


# Hash the contents of a file-like object.
def file_sha256(fileobj, _bufsize=2**18) -> str:
    digestobj = hashlib.sha256()

    if hasattr(fileobj, "getbuffer"):
        # io.BytesIO object, use zero-copy buffer
        digestobj.update(fileobj.getbuffer())
        return digestobj.hexdigest()

    # Only binary files implement readinto().
    if not (
        hasattr(fileobj, "readinto")
        and hasattr(fileobj, "readable")
        and fileobj.readable()
    ):
        raise ValueError(
            f"'{fileobj!r}' is not a file-like object in binary reading mode."
        )

    buf = bytearray(_bufsize)
    view = memoryview(buf)
    while True:
        size = fileobj.readinto(buf)
        if size == 0:
            break  # EOF
        digestobj.update(view[:size])

    return digestobj.hexdigest()
