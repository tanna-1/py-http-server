from ..http.request import HTTPRequest
from ..common import RequestHandler, to_http_date
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from datetime import datetime, timezone


class DefaultMiddleware(Middleware):
    def __init__(self, next: RequestHandler):
        super().__init__(next)

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        resp = self.next(requester, request)
        resp.headers = {
            "Server": "Tan's HTTP Server",
            "Date": to_http_date(datetime.now(timezone.utc)),
        } | resp.headers
        return resp
