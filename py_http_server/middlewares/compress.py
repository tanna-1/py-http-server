from typing import Any, Callable
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
        compression_threshold: int = 50,
    ):
        LOG.info(f"Enabled { ', '.join(ENCODINGS.keys())}")
        self.__compression_preferences = compression_preferences
        self.__compression_threshold = compression_threshold
        super().__init__(next)

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

        # Check if the response is compressible, file responses will not be compressed
        if (
            not resp.body
            or not resp.body.raw_content
            or len(resp.body.raw_content) < self.__compression_threshold
        ):
            return resp

        if encoding := self.__get_best_encoding(request):
            resp.body.raw_content = ENCODINGS[encoding](resp.body.raw_content)
            resp.headers["Content-Encoding"] = encoding

        return resp
