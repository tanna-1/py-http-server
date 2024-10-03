from http11.request import HTTPRequest
from networking.address import TCPAddress
from routers.base import Router, RouteHandler
import logging

LOG = logging.getLogger("routers.code")


def route(path):
    def _route_decorator(function):
        function._route = {"path": path}
        return function

    return _route_decorator


class CodeRouter(Router):
    def __init__(self) -> None:
        super().__init__(
            {
                "X-Powered-By": "Tan's HTTP Server",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )

        # Discover @route methods
        self.__handlers = {}  # type: dict[str, RouteHandler]
        for member in dir(self):
            value = getattr(self, member)
            if callable(value) and "_route" in dir(value):
                path = value._route["path"]
                LOG.debug(f'Discovered handler "{value.__qualname__}" for "{path}"')
                self.__handlers[path] = value

    def _handle(self, requester: TCPAddress, request: HTTPRequest):
        if not request.path in self.__handlers:
            return 404

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
            return 500
