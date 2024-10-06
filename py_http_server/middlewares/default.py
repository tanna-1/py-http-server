from ..http.constants import HEADER_DATE_FORMAT
from ..http.request import HTTPRequest
from ..common import RequestHandler
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from datetime import datetime, timezone


class DefaultMiddleware(Middleware):
    def __init__(self, next: RequestHandler) -> None:
        super().__init__(next)

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        resp = self.next(requester, request)
        resp.headers = {
            "Server": "Tan's HTTP Server",
            "Date": datetime.now(timezone.utc).strftime(HEADER_DATE_FORMAT),
        } | resp.headers
        return resp
