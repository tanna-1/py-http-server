from py_http_server.http.response_body import EmptyBody
from ..http.request import HTTPRequest
from ..common import RequestHandler, to_http_date
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from datetime import datetime, timezone


class DefaultMiddleware(Middleware):
    def __init__(self, next: RequestHandler):
        self.next = next

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        # Convert HEAD requests to GET
        original_method = request.method
        if original_method == "HEAD":
            request.method = "GET"

        resp = self.next(requester, request)
        resp.headers = {
            "Server": "Tan's HTTP Server",
            "Date": to_http_date(datetime.now(timezone.utc)),
        } | resp.headers

        # Omit the body if it was a HEAD request
        if original_method == "HEAD":
            resp.body = EmptyBody()

        return resp
