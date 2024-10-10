from typing import Union
from ..http.constants import NO_CACHE_HEADERS
from ..http.response import HTTPResponseFactory
from ..http.request import HTTPRequest
from ..common import RequestHandler
from ..networking.address import TCPAddress
from .base import Middleware


class VirtualHostMiddleware(Middleware):
    def __init__(self, next_map: dict[Union[str, None], RequestHandler]):
        self.next_map = next_map
        self.http = HTTPResponseFactory(NO_CACHE_HEADERS)

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        # Forward the request to correct host if host header is present and is a match
        if "host" in request.headers:
            host = request.headers["host"]
            if host in self.next_map:
                return self.next_map[host](requester, request)

        # Forward the request to default virtual host if there is one
        if None in self.next_map:
            return self.next_map[host](requester, request)

        # No match
        return self.http.status(404)
