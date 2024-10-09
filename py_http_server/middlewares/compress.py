from pathlib import Path
from typing import Any, Callable

from py_http_server.http.response_body import BytesBody, FileBody, ResponseBody
from ..http.request import HTTPRequest
from ..common import RequestHandler
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from .. import log

LOG = log.getLogger("middlewares.compress")
ENCODINGS = {}

try:
    import zlib  # type: ignore

    ENCODINGS["deflate"] = zlib.compress
except:
    pass

try:
    import brotli  # type: ignore

    ENCODINGS["br"] = brotli.compress
except:
    pass

try:
    import zstd  # type: ignore

    ENCODINGS["zstd"] = zstd.compress
except:
    pass

try:
    import gzip  # type: ignore

    ENCODINGS["gzip"] = ENCODINGS["x-gzip"] = gzip.compress
except:
    pass


class CompressMiddleware(Middleware):
    def __init__(
        self,
        next: RequestHandler,
        compression_preferences: list[str] = ["br", "zstd", "gzip", "x-gzip" "deflate"],
        min_response_size: int = 50,  # 50 bytes
        max_response_size: int = 10485760,  # 10 MiB
    ):
        super().__init__(next)
        LOG.info(f"Enabled { ', '.join(ENCODINGS.keys())}")
        self.__compression_preferences = compression_preferences
        self.__min_response_size = min_response_size
        self.__max_response_size = max_response_size

    def __get_best_encoding(self, request: HTTPRequest):
        mutual_encodings = []

        if "accept-encoding" in request.headers:
            for encoding in request.headers["accept-encoding"].split(","):
                encoding = encoding.lower().strip()
                if encoding in ENCODINGS:
                    mutual_encodings.append(encoding)

        # Pick the most preferred mutual encoding or None
        return next(
            (x for x in self.__compression_preferences if x in mutual_encodings), None
        )

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        resp = self.next(requester, request)

        # Return if response has no body
        if not resp.body:
            return resp

        # Return if response size is below min or above max threshold for compression
        if not (self.__min_response_size <= len(resp.body) <= self.__max_response_size):
            return resp

        if encoding := self.__get_best_encoding(request):
            resp.headers["Content-Encoding"] = encoding

            if isinstance(resp.body, BytesBody):
                # Directly compress bytes bodies
                resp.body.content = ENCODINGS[encoding](resp.body.content)
            elif isinstance(resp.body, FileBody):
                # Convert file bodies to bytes bodies for compression
                with resp.body.file_path.open("rb") as f:
                    resp.body = ResponseBody.from_bytes(ENCODINGS[encoding](f.read()))
            else:
                raise RuntimeError("Unsupported response content type")

        return resp
