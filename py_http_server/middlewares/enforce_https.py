from typing import Optional
from ..http.response import HTTPResponseFactory
from ..networking import ConnectionInfo
from ..http.request import HTTPRequest
from ..common import RequestHandler
from ..middlewares.base import Middleware


class EnforceHTTPSMiddleware(Middleware):
    def __init__(self, next: RequestHandler, hsts_max_age: Optional[int] = None):
        self.__hsts_max_age = hsts_max_age
        self.next = next
        self.http = HTTPResponseFactory()

    def __call__(self, conn_info: ConnectionInfo, request: HTTPRequest):
        resp = self.next(conn_info, request)

        hsts_header = {}
        if self.__hsts_max_age is not None:
            hsts_header = {
                "Strict-Transport-Security": f"max-age={self.__hsts_max_age}"
            }

        # Only redirect if the host value is known
        if not conn_info.secure and "host" in request.headers:
            return self.http.redirect(
                request.to_url(request.headers["host"], "https"),
                True,
                hsts_header,
            )

        # Set the HSTS header
        resp.headers = resp.headers | hsts_header
        return resp
