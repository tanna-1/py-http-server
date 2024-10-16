from ..http.constants import NO_CACHE_HEADERS
from ..http.request import HTTPRequest
from ..http.response import HTTPResponse, HTTPResponseFactory
from ..networking.address import TCPAddress
from ..routers.base import Router
from .. import log
from typing import Callable

LOG = log.getLogger("routers.code")


def route(path):
    def _route_decorator(function):
        function._route = {"path": path}
        return function

    return _route_decorator


class CodeRouter(Router):
    def __init__(self):
        self.http = HTTPResponseFactory(NO_CACHE_HEADERS)

        # Discover @route methods
        self.__handlers: dict[
            str, Callable[[TCPAddress, HTTPRequest], HTTPResponse]
        ] = {}
        for member in dir(self):
            value: Callable[[TCPAddress, HTTPRequest], HTTPResponse] = getattr(
                self, member
            )
            if callable(value) and "_route" in dir(value):
                path = value._route["path"]
                LOG.debug(f'Discovered handler "{value.__qualname__}" for "{path}"')
                self.__handlers[path] = value

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        if not request.path in self.__handlers:
            return self.default_route(requester, request)

        handler = self.__handlers[request.path]
        try:
            LOG.debug(
                f'Calling handler "{handler.__qualname__}" for path "{request.path}"'
            )
            return handler(requester, request)
        except Exception as exc:
            LOG.exception(
                f'Exception in handler for path "{request.path}"', exc_info=exc
            )
            return self.http.status(500)

    def default_route(self, requester: TCPAddress, request: HTTPRequest):
        return self.http.status(404)
